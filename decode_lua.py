# -*- coding: utf-8 -*-
import re
import binascii
from typing import Optional, Tuple
import codecs

def analyze_encoding(data: str) -> Tuple[str, set]:
    """Analyze possible encodings of a string"""
    encodings = set()
    
    # Test various encodings
    for enc in ['utf-8', 'utf-16', 'ascii', 'latin1', 'cp1252']:
        try:
            data.encode(enc)
            encodings.add(enc)
        except UnicodeEncodeError:
            continue
            
    return data, encodings

def decode_shifted_string(encoded: str) -> str:
    """Decode a string by shifting each character based on observed patterns"""
    result = []
    for c in encoded:
        # Special case mappings we've observed
        if c == 'f': result.append('g')  # f`ld -> game
        elif c == '`': result.append('a')
        elif c == 'l': result.append('m')
        elif c == 'd': result.append('e')
        elif c == 'F': result.append('G')  # FduRdswhbd -> GetService
        elif c == 'u': result.append('t')
        elif c == 'R': result.append('S')
        elif c == 's': result.append('r')
        elif c == 'w': result.append('v')
        elif c == 'h': result.append('i')
        elif c == 'b': result.append('c')
        else:
            result.append(c)
    return ''.join(result)

def decode_chunk(data: bytes, length: int) -> Tuple[str, int]:
    """Process a chunk of encoded data"""
    chunk = []
    pos = 0
    
    while pos < length and pos < len(data):
        if 32 <= data[pos] <= 126:  # Printable ASCII
            chunk.append(chr(data[pos]))
        pos += 1
        
    encoded_str = ''.join(chunk)
    if encoded_str:
        decoded_str = decode_shifted_string(encoded_str)
        print(f"\nFound chunk length {len(encoded_str)}:")
        print(f"Raw bytes: {' '.join(hex(x)[2:] for x in data[:length])}")
        print(f"Encoded: {encoded_str!r}")
        print(f"Decoded: {decoded_str!r}")
        return decoded_str, pos
    return "", pos

def decode_lua(encoded: str) -> Optional[str]:
    try:
        # Convert to bytes
        data = encoded.encode('latin1')
        chunks = []
        pos = 0
        
        # Handle header sequence \226\0\1\1\3\5\1\1\1
        if len(data) > 9 and data[0] == 0xe2:
            header = data[:9]
            print(f"\nHeader: {' '.join(hex(x)[2:] for x in header)}")
            pos = 9
        
        while pos < len(data):
            # Look for control sequence pattern
            if data[pos] <= 0x11:
                length = data[pos]
                control = data[pos:pos+5]
                print(f"\nControl sequence at pos {pos}: {' '.join(hex(x)[2:] for x in control)}")
                pos += 5
                
                # Process the chunk
                chunk, chunk_len = decode_chunk(data[pos:], length)
                if chunk:
                    chunks.append(chunk)
                pos += chunk_len
            else:
                pos += 1
                
        return '\n'.join(chunks)
        
    except Exception as e:
        print(f"Error decoding: {e}")
        traceback.print_exc()
        return None

def decode_O(encoded_str: str) -> Optional[str]:
    print(f"Starting decode_O with input length: {len(encoded_str)}")
    A, e, D = "", "", []
    K = 256
    B = [chr(C) for C in range(K)]
    C = 0
    string_positions = []  # Track where strings start
    current_string = []    # Buffer for current string

    def X() -> int:
        nonlocal C
        try:
            # Base-36 decoding
            A = int(encoded_str[C], 36)
            C += 1
            e = int(encoded_str[C:C + A], 36)
            C += A
            if len(current_string) > 0:  # If we've been building a string
                joined = ''.join(current_string)
                if joined:  # If it's not empty
                    print(f"Found potential string: {joined}")
                current_string.clear()
            return e
        except ValueError as ve:
            print(f"Base-36 decoding error: {ve}")
            return 0

    try:
        # Get first character
        initial = X()
        A = chr(initial)
        print(f"Initial character: {A!r} (0x{initial:02x})")
        D.append(A)
        
        # Main decoding loop
        while C < len(encoded_str):
            C_val = X()
            
            if C_val < len(B):
                e = B[C_val]
                # Check if this could be start of "game:GetService"
                if e == 'g' or e == 'G':
                    string_positions.append(len(D))
            else:
                e = A + A[0]

            B.append(A + e[0])
            D.append(e)
            A = e
            
            # Add to current string buffer if printable
            if e.isprintable():
                current_string.append(e)
            elif len(current_string) > 0:
                joined = ''.join(current_string)
                if joined:
                    print(f"Found string: {joined}")
                current_string.clear()

            # Print progress every 1000 iterations
            if len(D) % 1000 == 0:
                print(f"Decoded {len(D)} characters...")
        
        # Check any remaining string buffer
        if len(current_string) > 0:
            joined = ''.join(current_string)
            if joined:
                print(f"Found final string: {joined}")

        result = ''.join(D)
        print(f"Decoding complete. Result length: {len(result)}")
        
        # Check positions where we found potential strings
        for pos in string_positions:
            substr = ''.join(D[pos:pos+15])  # Check reasonable string length
            if "game:GetService" in substr:
                print(f"Found target string at position {pos}: {substr}")
        
        return result
        
    except Exception as ex:
        print(f"Error during decoding: {ex}")
        return None

if __name__ == "__main__":
    with open('test.lua', 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract the encoded string
    match = re.search(r"O\('([^']+)'\)", content)
    if match:
        encoded_string = match.group(1)
        print(f"Found encoded string, length: {len(encoded_string)}")
        hex_result = decode_lua(encoded_string)
        
        if hex_result:
            # Save decoded output for further analysis
            with open('decoded_output.bin', 'wb') as f:
                f.write(bytes.fromhex(hex_result))
            print("\nDecoded output saved to decoded_output.bin")
    else:
        print("Encoded string not found in test.lua")

