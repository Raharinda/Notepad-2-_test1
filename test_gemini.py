#!/usr/bin/env python3
"""Quick test for Gemini integration"""

from utils import gemini_client

print('Testing Gemini text generation...')
test_prompt = 'Say hello'
result = gemini_client.generate_text(test_prompt)
print(f'Result: {result}')
print(f'Type: {type(result)}')

if result and isinstance(result, str):
    print('✅ Gemini generation working!')
else:
    print('⚠️ Gemini might have issues or no API key')
