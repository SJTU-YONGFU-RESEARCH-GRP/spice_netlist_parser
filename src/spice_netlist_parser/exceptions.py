"""Custom exceptions for SPICE netlist parsing."""

from typing import Optional


class ParseError(Exception):
    """Exception raised when netlist parsing fails.
    
    Attributes:
        filename: Name of the file being parsed (if applicable)
        line_number: Line number where the error occurred
        message: Error message describing what went wrong
    """
    
    def __init__(
        self,
        message: str,
        filename: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> None:
        """Initialize ParseError.
        
        Args:
            message: Error message describing the issue
            filename: Optional filename where error occurred
            line_number: Optional line number where error occurred
        """
        self.filename = filename
        self.line_number = line_number
        formatted_message = self._format_message(message)
        super().__init__(formatted_message)
    
    def _format_message(self, message: str) -> str:
        """Format error message with file and line information.
        
        Args:
            message: Base error message
            
        Returns:
            Formatted error message with context
        """
        parts = []
        if self.filename:
            parts.append(f"File: {self.filename}")
        if self.line_number:
            parts.append(f"Line {self.line_number}")
        parts.append(message)
        return " - ".join(parts)


class ValidationError(Exception):
    """Exception raised when netlist validation fails.
    
    This exception is used for semantic validation errors after successful
    parsing, such as missing nodes, invalid component connections, etc.
    
    Attributes:
        message: Error message describing the validation failure
    """
    
    def __init__(self, message: str) -> None:
        """Initialize ValidationError.
        
        Args:
            message: Error message describing the validation failure
        """
        self.message = message
        super().__init__(message)


