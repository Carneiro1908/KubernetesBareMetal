import subprocess
import time
import urllib.request
import json
import os
import signal
import sys

SERVER_URL = "http://localhost:8000"

def run_tests():
    print("=== Starting API REST Integration Tests ===")
    
    # Start the FastAPI server in the background
    server_process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid if hasattr(os, 'setsid') else None # Clean process termination on Unix
    )
    
    # Wait for the server to spin up
    time.sleep(2.0)
    
    try:
        # Test 1: Access main index page (Static HTML serving verification)
        print("Test 1: Requesting GET / ...", end=" ")
        req = urllib.request.Request(f"{SERVER_URL}/")
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            html_content = res.read().decode('utf-8')
            assert "<title>Antigravity Finance" in html_content
            print("PASSED ✅")

        # Test 2: Fetch seed transactions
        print("Test 2: Requesting GET /api/transactions ...", end=" ")
        req = urllib.request.Request(f"{SERVER_URL}/api/transactions")
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            transactions = json.loads(res.read().decode('utf-8'))
            assert isinstance(transactions, list)
            assert len(transactions) > 0
            print(f"PASSED ✅ ({len(transactions)} transactions found)")

        # Test 3: Add a new transaction record via POST
        print("Test 3: Requesting POST /api/transactions ...", end=" ")
        payload = {
            "description": "Integration Test Espresso",
            "amount": 4.50,
            "type": "expense",
            "category": "Food",
            "date": "2026-06-29"
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{SERVER_URL}/api/transactions",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        new_transaction_id = None
        with urllib.request.urlopen(req) as res:
            assert res.status == 201
            resp_body = json.loads(res.read().decode('utf-8'))
            assert resp_body["success"] is True
            assert "id" in resp_body
            new_transaction_id = resp_body["id"]
            print(f"PASSED ✅ (ID Created: {new_transaction_id})")

        # Test 4: Retrieve computed stats via GET
        print("Test 4: Requesting GET /api/stats ...", end=" ")
        req = urllib.request.Request(f"{SERVER_URL}/api/stats")
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            stats = json.loads(res.read().decode('utf-8'))
            assert "total_income" in stats
            assert "total_expense" in stats
            assert "net_balance" in stats
            assert "categories" in stats
            assert "Food" in stats["categories"]
            print("PASSED ✅")

        # Test 5: Retrieve metrics endpoint for Prometheus
        print("Test 5: Requesting GET /metrics ...", end=" ")
        req = urllib.request.Request(f"{SERVER_URL}/metrics")
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            metrics_body = res.read().decode('utf-8')
            assert "http_requests_total" in metrics_body
            print("PASSED ✅")

        # Test 6: Delete the newly created transaction
        print(f"Test 6: Requesting DELETE /api/transactions?id={new_transaction_id} ...", end=" ")
        req = urllib.request.Request(
            f"{SERVER_URL}/api/transactions?id={new_transaction_id}",
            method="DELETE"
        )
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            resp_body = json.loads(res.read().decode('utf-8'))
            assert resp_body["success"] is True
            print("PASSED ✅")

        print("\n🎉 All 6 API integration tests passed successfully! 🎉")
        
    except Exception as e:
        print(f"FAILED ❌")
        print(f"Error details: {e}")
        # Capture server error logs on failure
        try:
            stdout, stderr = server_process.communicate(timeout=1.0)
            if stderr:
                print("Server Error Logs:")
                print(stderr.decode('utf-8'))
        except Exception:
            pass
        sys.exit(1)
        
    finally:
        # Clean shutdown of server
        print("Shutting down test server...")
        try:
            if hasattr(os, 'killpg'):
                os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
            else:
                server_process.terminate()
        except Exception:
            try:
                server_process.kill()
            except Exception:
                pass
            
if __name__ == "__main__":
    run_tests()
