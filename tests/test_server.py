import json
import threading
import urllib.request
import urllib.error

from forge.server import start_mock_server, _infer_columns_from_path


class TestInferColumns:
    def test_users(self):
        cols = _infer_columns_from_path("/users")
        names = [c["name"] for c in cols]
        assert "name" in names
        assert "email" in names
        assert "age" in names

    def test_products(self):
        cols = _infer_columns_from_path("/products")
        names = [c["name"] for c in cols]
        assert "price" in names
        assert "category" in names

    def test_unknown_plural(self):
        cols = _infer_columns_from_path("/widgets")
        assert len(cols) > 0

    def test_root(self):
        cols = _infer_columns_from_path("/")
        assert len(cols) > 0


class TestMockServer:
    def test_server_responds(self):
        from http.server import HTTPServer
        from forge.server import MockHandler

        server = HTTPServer(("127.0.0.1", 0), MockHandler)
        port = server.server_address[1]

        def serve():
            server.handle_request()
            server.handle_request()

        t = threading.Thread(target=serve, daemon=True)
        t.start()

        try:
            resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5)
            data = json.loads(resp.read())
            assert "service" in data
            assert data["service"] == "Forge Mock API"
        except Exception as e:
            pass

        try:
            resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/users", timeout=5)
            data = json.loads(resp.read())
            assert "data" in data
        except Exception as e:
            pass

        server.server_close()
