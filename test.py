import requests
import csv
import io

# 最新の1時間降水量データ
CSV_URL = "https://www.data.jma.go.jp/stats/data/mdrr/pre_rct/alltable/pre1h00_rct.csv"

def main():
    # 1) CSVをHTTP取得
    r = requests.get(CSV_URL, timeout=20)
    r.raise_for_status()

    # 気象庁CSVは Shift_JIS → 文字化け防止に指定
    r.encoding = "shift_jis"
    
    f = io.StringIO(r.text)
    reader = csv.reader(f)

    # 2) ヘッダを読む
    header = next(reader)
    print("header:", header)

    print("\n福岡県の観測データ（先頭10件）:")

    # 3) 福岡県の行だけ
    count = 0
    for row in reader:
        # 都道府県列が '福岡県' のみ
        if len(row) >= 2 and row[1] == "福岡県":
            print(row)
            count += 1
            if count >= 10:
                break

    if count == 0:
        print("福岡県のデータがありませんでした。")

if __name__ == "__main__":
    main()
