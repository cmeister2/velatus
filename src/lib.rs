use std::borrow::Cow;

use log::debug;
use pyo3::{prelude::*, types::PyString};
use regex::{escape, Regex};

// Create a logging Formatter that masks secrets.
#[pyclass]
struct SecretFormatter {
    regex: Regex,
    formatter: Py<PyAny>,
    mask: String,
}

#[pymethods]
impl SecretFormatter {
    /// Create a new SecretFormatter instance.
    #[new]
    #[pyo3(signature = (secrets, mask=None, existing_formatter=None))]
    pub fn new(
        py: Python<'_>,
        secrets: Vec<Bound<PyString>>,
        mask: Option<String>,
        existing_formatter: Option<Py<PyAny>>,
    ) -> PyResult<Self> {
        Self::construct(py, secrets, mask, existing_formatter)
    }

    /// Format the log record and mask secrets in the resulting message.
    pub fn format(&self, py: Python<'_>, record: Bound<PyAny>) -> PyResult<String> {
        // Format the log record using the underlying formatter
        let formatter = self.formatter.bind(py);
        let formatted = formatter
            .call_method1("format", (record,))?
            .unbind();
        let formatted = formatted.bind(py);

        // Get the formatted message as a string
        let message = if let Ok(string) = formatted.downcast::<PyString>() {
            string.extract::<String>()?
        } else {
            // The response from the formatter should be a string, but if it's not, fall back to calling str()
            formatted.str()?.extract::<String>()?
        };

        Ok(self.redact(message))
    }

    /// Redact secrets from exceptions and write the traceback to stderr.
    pub fn handle_exception(
        &self,
        py: Python<'_>,
        exc_type: Bound<PyAny>,
        exc_value: Bound<PyAny>,
        exc_traceback: Option<Bound<PyAny>>,
    ) -> PyResult<()> {
        let original_message = exc_value.str()?.extract::<String>()?;
        let redacted_message = self.redact(original_message);
        let redacted_exception = exc_type.call1((redacted_message.clone(),))?;

        let traceback_module = py.import("traceback")?;

        let tb_lines: Vec<String> = traceback_module
            .call_method1(
                "format_exception",
                (exc_type, redacted_exception, exc_traceback),
            )?
            .extract()?;

        let joined = tb_lines.join("");
        let sys_module = py.import("sys")?;
        let stderr = sys_module.getattr("stderr")?;
        stderr.call_method1("write", (joined,))?;

        Ok(())
    }
}

impl SecretFormatter {
    fn construct(
        py: Python<'_>,
        secrets: Vec<Bound<PyString>>,
        mask: Option<String>,
        existing_formatter: Option<Py<PyAny>>,
    ) -> PyResult<Self> {
        let escaped: PyResult<Vec<String>> = secrets
            .into_iter()
            .map(|s| s.extract::<&str>().map(escape))
            .collect();

        let secrets = escaped?;

        if secrets.is_empty() {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "At least one secret must be provided",
            ));
        }

        debug!("Creating secret formatter for {} secrets", secrets.len());

        let pattern = secrets.join("|");

        let pattern = format!("({pattern})");
        let regex = Regex::new(&pattern)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

        let formatter = match existing_formatter {
            Some(f) => f,
            None => {
                let logging = py.import("logging")?;
                logging
                    .getattr("Formatter")?
                    .call0()?
                    .unbind()
            }
        };

        Ok(SecretFormatter {
            regex,
            formatter,
            mask: mask.unwrap_or_else(|| "[MASKED]".to_string()),
        })
    }

    fn redact(&self, message: String) -> String {
        // Replace any regex matches with the mask
        //
        // Rely on the fact that regex::Regex::replace_all returns
        // Cow::Borrowed if no matches are found, and Cow::Owned if matches are found
        // to be faster against normal lines which need no masking
        match self.regex.replace_all(&message, &self.mask) {
            Cow::Borrowed(_) => {
                // No matches found, do nothing
                message
            },
            Cow::Owned(masked_msg) => {
                // Return the replacement string.
                masked_msg
            }
        }
    }
}

/// Velatus: A Python module for masking sensitive information in log messages.
#[pymodule]
fn velatus(m: &Bound<'_, PyModule>) -> PyResult<()> {
    pyo3_log::init();
    m.add_class::<SecretFormatter>()?;
    Ok(())
}
