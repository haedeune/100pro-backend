"""
애플리케이션 실행 진입점.
`python -m main` 또는 `uvicorn app.main:app --reload` 로 서버 기동.
"""
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
