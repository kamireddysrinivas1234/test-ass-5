from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from .database import Base, engine, SessionLocal
from .routers import users, calculations
from . import crud_users, schemas

Base.metadata.create_all(bind=engine)

def seed_demo_user() -> None:
    db = SessionLocal()
    try:
        existing = crud_users.get_user_by_username(db, "demo")
        if not existing:
            demo_user = schemas.UserCreate(
                username="demo",
                email="demo@example.com",
                password="Test123!",
            )
            crud_users.create_user(db, demo_user)
    finally:
        db.close()

seed_demo_user()

app = FastAPI(title="User & Calculation API")
app.include_router(users.router)
app.include_router(calculations.router)

CALC_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>FastAPI Calculator with Login</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto;
           padding: 20px; border: 1px solid #ddd; border-radius: 8px; background:#fafafa; }
    h1 { margin-top: 0; }
    label { display:block; margin-top:10px; }
    input, select, button { padding:8px; margin-top:5px; width:100%; box-sizing:border-box; }
    button { margin-top:15px; cursor:pointer; }
    #result-box { margin-top:20px; padding:10px; border-radius:6px; background:#f4f4f4; }
    .error { color:#b00020; }
    .ok { color:#007700; }
  </style>
</head>
<body>
  <h1>FastAPI Calculator (with Login)</h1>
  <p>This page logs in to your API and then calls the <code>/calculations/</code> endpoint.</p>
  <h2>Step 1: Login</h2>
  <p>
    Demo credentials already created:<br/>
    <strong>Username:</strong> <code>demo</code>,
    <strong>Password:</strong> <code>Test123!</code>
  </p>
  <label for="username">Username:</label>
  <input id="username" type="text" value="demo" />
  <label for="password">Password:</label>
  <input id="password" type="password" value="Test123!" />
  <button id="login-btn">Login</button>
  <p id="login-status"></p>
  <hr/>
  <h2>Step 2: Calculator</h2>
  <label for="a">First number (a):</label>
  <input type="number" id="a" step="any" />
  <label for="b">Second number (b):</label>
  <input type="number" id="b" step="any" />
  <label for="type">Operation:</label>
  <select id="type">
    <option value="add">Add</option>
    <option value="sub">Subtract</option>
    <option value="mul">Multiply</option>
    <option value="div">Divide</option>
  </select>
  <button id="calc-btn">Calculate</button>
  <div id="result-box">
    <strong>Result:</strong> <span id="result-value">N/A</span>
    <div id="calc-error" class="error"></div>
  </div>
  <p>API docs are at <a href="/docs" target="_blank">/docs</a>.</p>
  <script>
    let accessToken = null;
    const loginStatus = document.getElementById('login-status');
    const resultSpan = document.getElementById('result-value');
    const calcError = document.getElementById('calc-error');
    document.getElementById('login-btn').addEventListener('click', async () => {
      const username = document.getElementById('username').value.trim();
      const password = document.getElementById('password').value.trim();
      loginStatus.textContent = ''; loginStatus.className = '';
      if (!username || !password) {
        loginStatus.textContent = 'Please enter username and password.'; loginStatus.className = 'error'; return;
      }
      try {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        const response = await fetch('/users/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData.toString()
        });
        if (!response.ok) {
          const err = await response.json().catch(() => ({}));
          loginStatus.textContent = err.detail || 'Login failed.'; loginStatus.className = 'error'; accessToken = null; return;
        }
        const data = await response.json();
        accessToken = data.access_token;
        loginStatus.textContent = 'Login successful. You can now calculate.'; loginStatus.className = 'ok';
      } catch (e) {
        console.error(e);
        loginStatus.textContent = 'Network error during login.'; loginStatus.className = 'error';
      }
    });
    document.getElementById('calc-btn').addEventListener('click', async () => {
      calcError.textContent = ''; resultSpan.textContent = '...';
      if (!accessToken) { calcError.textContent = 'Please login first using the demo credentials.'; resultSpan.textContent = 'N/A'; return; }
      const aValue = document.getElementById('a').value;
      const bValue = document.getElementById('b').value;
      const typeValue = document.getElementById('type').value;
      if (aValue === '' || bValue === '') { calcError.textContent = 'Please enter both numbers.'; resultSpan.textContent = 'N/A'; return; }
      try {
        const payload = { type: typeValue, a: parseFloat(aValue), b: parseFloat(bValue) };
        const response = await fetch('/calculations/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + accessToken
          },
          body: JSON.stringify(payload)
        });
        if (!response.ok) {
          const err = await response.json().catch(() => ({}));
          calcError.textContent = err.detail || 'Error performing calculation.'; resultSpan.textContent = 'N/A'; return;
        }
        const data = await response.json();
        resultSpan.textContent = data.result;
      } catch (e) {
        console.error(e);
        calcError.textContent = 'Network or server error.'; resultSpan.textContent = 'N/A';
      }
    });
  </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def root_calc_page():
    return CALC_HTML
