import zmq
import json
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

# Configuration (Must match C++ Generator)
AES_KEY = b"01234567890123456789012345678901"
AES_IV = b"0123456789012345"

def decrypt_message(encrypted_b64):
    try:
        # 1. Decode Base64
        encrypted_bytes = base64.b64decode(encrypted_b64)
        
        # 2. Decrypt AES-256-CBC
        cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_padded = decryptor.update(encrypted_bytes) + decryptor.finalize()
        
        # 3. Remove Padding (PKCS7 is standard, but C++ OpenSSL might just be zero-padding or handled by EVP)
        # The C++ EVP_EncryptFinal_ex handles PKCS7 padding by default.
        # We need to unpad it here.
        # However, let's try to just decode utf-8 first, sometimes C++ strings are null terminated.
        # Let's use cryptography's unpadder for safety.
        
        # Note: C++ EVP_EncryptFinal_ex adds PKCS7 padding.
        # Block size for AES is 128 bits (16 bytes)
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(decrypted_padded) + unpadder.finalize()
        
        return data.decode('utf-8')
    except Exception as e:
        print(f"Decryption Error: {e}")
        return None

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://127.0.0.1:5555") 
socket.setsockopt_string(zmq.SUBSCRIBE, "") # Subscribe to EVERYTHING

print("Listening for SECURE EEG Stream...")

while True:
    # Receive raw string: "EEG_SECURE {base64_data}"
    message = socket.recv_string()
    
    # Strip Topic ("EEG_SECURE ") to get Base64 payload
    encrypted_b64 = message[11:] 
    
    json_str = decrypt_message(encrypted_b64)
    
    if json_str:
        try:
            data = json.loads(json_str)
            # Calculate a simple "Focus Ratio" (Beta / Theta)
            theta = data['eeg']['theta']
            beta = data['eeg']['beta']
            
            focus_ratio = beta / theta if theta > 0 else 0
            
            print(f"Timestamp: {data['timestamp']} | Focus Ratio: {focus_ratio:.2f}")
            
        except Exception as e:
            print(f"JSON Parsing Error: {e} | Raw: {json_str}")