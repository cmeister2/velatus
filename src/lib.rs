use std::borrow::Cow;

use log::debug;
use pyo3::{prelude::*, types::{PyBytes, PyString}};
use regex::{escape, Regex};

// Create a callable class that stores a masking regex
#[pyclass]
struct Masker {
    regex: Regex,
    mask: String,
}

#[pymethods]
impl Masker {
    /// Create a new Masker instance.
    #[new]
    #[pyo3(signature = (strings, mask=None))]
    pub fn new(strings: Vec<Bound<PyString>>, mask: Option<Bound<PyString>>) -> PyResult<Self> {
        // Convert the PyString objects to Rust strings, escaping them for regex
        let res: PyResult<Vec<String>> = strings
            .into_iter()
            .map(|s| s.extract::<&str>().map(escape))
            .collect();

        let strings: Vec<String> = res?;

        // Fail if no strings are provided
        if strings.is_empty() {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "At least one string must be provided",
            ));
        }

        debug!("Creating masker for {} strings", strings.len());

        // If a mask is provided, use it; otherwise, default to [MASKED]
        let mask = match mask {
            Some(m) => m.extract::<String>()?,
            None => "[MASKED]".to_string(),
        };

        // Join the strings with '|' to create a regex pattern
        let pattern = format!("({})", strings.join("|"));
        let regex = Regex::new(&pattern)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("{}", e)))?;

        Ok(Masker { regex, mask })
    }

    /// Mask the log record's message using the regex.
    pub fn __call__(&self, log_record: Bound<PyAny>) -> PyResult<bool> {
        // The log_record is expected to be a logging.LogRecord object
        // Extract the message from the log_record
        let msg_attr = log_record.getattr("msg")?;

        let msg = if let Ok(string) = msg_attr.downcast::<PyString>() {
            // If the message is a string, extract it directly
            string.extract::<String>()?
        } else if let Ok(bytes) = msg_attr.downcast::<PyBytes>() {
            // If the message is a bytes object, decode it to a string and extract it
            // This is necessary because the regex operates on strings
            bytes.call_method1("decode", ("utf-8",))?.extract::<String>()?
        }
        else {
            // If the message is neither a string nor bytes, call str() on the object
            msg_attr.call_method0("__str__")?.extract::<String>()?
        };

        // Replace any regex matches with the mask
        //
        // Rely on the fact that regex::Regex::replace_all returns
        // Cow::Borrowed if no matches are found, and Cow::Owned if matches are found
        // to be faster against normal lines which need no masking
        match self.regex.replace_all(&msg, &self.mask) {
            Cow::Borrowed(_) => {
                // No matches found, do nothing
            },
            Cow::Owned(masked_msg) => {
                // Set the masked message back to the log_record
                log_record.setattr("msg", masked_msg)?;
            }
        }
        Ok(true)
    }
}

/// Velatus: A Python module for masking sensitive information in log messages.
#[pymodule]
fn velatus(m: &Bound<'_, PyModule>) -> PyResult<()> {
    pyo3_log::init();
    m.add_class::<Masker>()?;
    Ok(())
}
