# GUI 표시용 한국어 라벨 매핑표(by_type / by_risk / by_age)

BY_TYPE_KO = {
    "Logs": "로그",
    "Build": "빌드 산출물",
    "Cache": "캐시",
    "Temp": "임시 파일",
    "临时/构建产物": "임시,빌드 산출물",
    "日志文件": "로그 파일",
    "缓存文件": "캐시 파일",
    "备份文件": "백업 파일",
    "下载文件": "다운로드 파일",
    "媒体文件": "미디어 파일",
    "文档文件": "문서 파일",
    "压缩文件": "압축 파일",
    "其他文件": "기타 파일",
}

BY_RISK_KO = {
    "safe": "안전",
    "confirm_needed": "검토",
    "protected": "보호",
}

BY_AGE_KO = {
    "最近创建 (7天内)": "최근 생성 (7일 이내)",
    "近期文件 (30天内)": "최근 파일 (30일 이내)",
    "陈旧文件 (90天内)": "오래된 파일 (90일 이내)",
    "很旧 (90天以上)": "매우 오래됨 (90일 이상)",
}

# 원본 dict의 key를 한국어로 바꿔서 새 dict 반환
# 매핑표 없는 키는 그대로 반환 / 경고 -> 확인 후 그때마다 매핑 추가
def to_ko(category_dict: dict, mapping: dict) -> dict:
    result = {}
    for key, value in category_dict.items():
        ko_key = mapping.get(key)
        if ko_key is None:
            print(f"[WARN] 매핑표에 없는 라벨 발견: {key!r}")
            ko_key = key
        result[ko_key] = value
    return result
