"""Simple test endpoint for Vercel"""

def handler(request):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': '{"status": "ok", "message": "Python function works!"}'
    }
