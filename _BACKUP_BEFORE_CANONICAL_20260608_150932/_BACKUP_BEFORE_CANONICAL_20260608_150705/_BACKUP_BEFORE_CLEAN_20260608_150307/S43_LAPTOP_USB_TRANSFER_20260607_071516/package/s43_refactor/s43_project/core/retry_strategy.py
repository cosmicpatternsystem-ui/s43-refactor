class RetryStrategy(enum.Enum):
    IMMEDIATE = "immediate"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"
    FIXED = "fixed"