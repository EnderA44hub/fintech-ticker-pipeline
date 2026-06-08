@echo off
echo Levantando servidor del motor...
cd /d C:\Users\Ender A\Desktop\backtest_pipeline
start "" http://localhost:8080/motor/index.html
python -m http.server 8080