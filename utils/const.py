logs = {
        "dh": {"dir": "logs/dh/", "data": ["log_dh_128", "log_dh_192", "log_dh_256"], "name": "Diffie-Hellman Experiments"},
        "aes": {"dir": "logs/aes/", "data": ["log_encdec_time_128", "log_encdec_time_192", "log_encdec_time_256"], "name": "AES Encryption/Decryption Time"},
        "no-aes": {"dir": "logs/aes/"}
}

colors = {
        "log_dh_128": "black",
        "log_dh_192": "red",
        "log_dh_256": "purple",
        "log_encdec_time_128": "black",
        "log_encdec_time_192": "red",
        "log_encdec_time_256": "purple"
}
