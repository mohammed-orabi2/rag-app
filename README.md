# counselling-bot
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./static/studentgator.png">
  <img alt="Shows a black Browser Use Logo in light color mode and a white one in dark color mode." 
    src="./static/studentgator.png" 
    style="width: 50%;"
    align="center">
</picture>

<h1 align="left">Student Gator counselling bot 🤖</h1>
---

## Setup

- You need to run docker file `docker-compose`
- Run Fastapi server:
```bash
uvicorn integration.fastapi_server:app --reload --host 0.0.0.0 --port 8000
# Make sure port number a same with frontend
```
If you need open GUI 
- open another terminal and run this commend
```bash
python -m http.server 3000
```

**Make sure a database is connected it's very important.**



