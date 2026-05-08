//! Velatus: A Python module for masking sensitive information in log messages.

use std::collections::HashSet;

use aho_corasick::{AhoCorasick, AhoCorasickBuilder, MatchKind};
use log::debug;
use pyo3::{prelude::*, types::PyString};

/// A logging Formatter that masks secrets using Aho-Corasick matching.
#[pyclass]
struct SecretFormatter {
    /// Multi-pattern matcher built from the secret strings.
    matcher: AhoCorasick,
    /// The underlying Python logging formatter.
    formatter: Py<PyAny>,
    /// Replacement text for masked secrets.
    mask: String,
}

#[pymethods]
impl SecretFormatter {
    /// Create a new SecretFormatter instance.
    #[new]
    #[pyo3(signature = (secrets, mask=None, existing_formatter=None))]
    fn new(
        py: Python<'_>,
        secrets: Vec<Bound<PyString>>,
        mask: Option<String>,
        existing_formatter: Option<Py<PyAny>>,
    ) -> PyResult<Self> {
        let secrets = normalize_secrets(secrets)?;

        debug!("Creating secret formatter for {} secrets", secrets.len());

        let matcher = AhoCorasickBuilder::new()
            .match_kind(MatchKind::LeftmostLongest)
            .build(secrets.iter().map(String::as_str))
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

        let formatter = match existing_formatter {
            Some(formatter) => formatter,
            None => {
                let logging = py.import("logging")?;
                logging.getattr("Formatter")?.call0()?.unbind()
            }
        };

        Ok(SecretFormatter {
            matcher,
            formatter,
            mask: mask.unwrap_or_else(|| "[MASKED]".to_string()),
        })
    }

    /// Format the log record and mask secrets in the resulting message.
    fn format(&self, py: Python<'_>, record: Bound<PyAny>) -> PyResult<String> {
        let message = format_record(&self.formatter, py, record)?;
        Ok(self.redact(message))
    }

    /// Redact secrets from exceptions and write the traceback to stderr.
    fn handle_exception(
        &self,
        py: Python<'_>,
        exc_type: Bound<PyAny>,
        exc_value: Bound<PyAny>,
        exc_traceback: Option<Bound<PyAny>>,
    ) -> PyResult<()> {
        let traceback_module = py.import("traceback")?;
        let tb_lines: Vec<String> = traceback_module
            .call_method1("format_exception", (exc_type, exc_value, exc_traceback))?
            .extract()?;

        let joined = tb_lines.join("");
        let redacted = self.redact(joined);
        let sys_module = py.import("sys")?;
        let stderr = sys_module.getattr("stderr")?;
        stderr.call_method1("write", (redacted,))?;

        Ok(())
    }

    /// Replace all secret occurrences in `message` with the mask string.
    fn redact(&self, message: String) -> String {
        let mut matches = self.matcher.find_iter(&message).peekable();

        if matches.peek().is_none() {
            return message;
        }

        let mut masked = String::with_capacity(message.len());
        let mut last_end = 0;

        for mat in matches {
            masked.push_str(&message[last_end..mat.start()]);
            masked.push_str(&self.mask);
            last_end = mat.end();
        }

        masked.push_str(&message[last_end..]);
        masked
    }
}

/// Extract, validate, and deduplicate the list of secret strings.
fn normalize_secrets(secrets: Vec<Bound<PyString>>) -> PyResult<Vec<String>> {
    let mut secrets = secrets
        .into_iter()
        .map(|secret| secret.extract::<String>())
        .collect::<PyResult<Vec<_>>>()?;

    if secrets.is_empty() {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "At least one secret must be provided",
        ));
    }

    if secrets.iter().any(String::is_empty) {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "Secrets must not be empty strings",
        ));
    }

    let mut seen = HashSet::new();
    secrets.retain(|secret| seen.insert(secret.clone()));

    Ok(secrets)
}

/// Delegate to the Python formatter and return the resulting string.
fn format_record(formatter: &Py<PyAny>, py: Python<'_>, record: Bound<PyAny>) -> PyResult<String> {
    let formatter = formatter.bind(py);
    let formatted = formatter.call_method1("format", (record,))?.unbind();
    let formatted = formatted.bind(py);

    if let Ok(string) = formatted.cast::<PyString>() {
        string.extract::<String>()
    } else {
        formatted.str()?.extract::<String>()
    }
}

/// Velatus: A Python module for masking sensitive information in log messages.
#[pymodule]
fn velatus(m: &Bound<'_, PyModule>) -> PyResult<()> {
    pyo3_log::init();
    m.add_class::<SecretFormatter>()?;
    Ok(())
}
