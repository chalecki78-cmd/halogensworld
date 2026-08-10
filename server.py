import http.server
import json
import os
import socketserver

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.path.join(BASE_DIR, "current_session.json")
USERS_FILE = os.path.join(BASE_DIR, "users.json")


def load_users():
  if os.path.exists(USERS_FILE):
    try:
      with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except:
      return {}
  return {}


def save_users(users):
  with open(USERS_FILE, "w", encoding="utf-8") as f:
    json.dump(users, f, indent=4)


class JetsonHandler(http.server.SimpleHTTPRequestHandler):

  def do_POST(self):
    content_length = int(self.headers.get("Content-Length", 0))
    post_data = self.rfile.read(content_length)

    try:
      data = json.loads(post_data.decode("utf-8"))
    except:
      data = {}

    # Obsługa logowania / rejestracji / sesji
    if self.path == "/api/session":
      username = data.get("user", "GUEST")
      with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump({"logged_user": username}, f, indent=4)

      self.send_response(200)
      self.send_header("Content-Type", "application/json")
      self.end_headers()
      self.wfile.write(
          json.dumps({"status": "success", "user": username}).encode("utf-8")
      )

    elif self.path == "/api/register":
      username = data.get("user", "").strip()
      password = data.get("pass", "")

      users = load_users()
      if not username or not password:
        res = {"status": "error", "message": "empty"}
      elif username in users:
        res = {"status": "error", "message": "exists"}
      else:
        users[username] = password
        save_users(users)
        res = {"status": "success"}

      self.send_response(200)
      self.send_header("Content-Type", "application/json")
      self.end_headers()
      self.wfile.write(json.dumps(res).encode("utf-8"))

    elif self.path == "/api/login":
      username = data.get("user", "").strip()
      password = data.get("pass", "")

      users = load_users()
      if username in users and users[username] == password:
        res = {"status": "success", "user": username}
      else:
        res = {"status": "error", "message": "invalid"}

      self.send_response(200)
      self.send_header("Content-Type", "application/json")
      self.end_headers()
      self.wfile.write(json.dumps(res).encode("utf-8"))

    else:
      self.send_response(404)
      self.end_headers()


if __name__ == "__main__":
  # Czyszczenie starej sesji przy starcie serwera
  if os.path.exists(SESSION_FILE):
    os.remove(SESSION_FILE)

  print(f"Serwer Jetson uruchomiony na porcie {PORT}")
  with socketserver.TCPServer(("", PORT), JetsonHandler) as httpd:
    try:
      httpd.serve_forever()
    except KeyboardInterrupt:
      pass