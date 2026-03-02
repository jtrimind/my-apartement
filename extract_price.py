import duckdb

def process_price_data():
    pub_price_file = '국토교통부_주택 공시가격 정보(2025).csv'
    apt_basic_file = 'apt_basic.csv'
    output_csv = 'apt_price_mapped.csv'

    print('도로명주소를 기준으로 조인 및 데이터 추출을 시작합니다...')

    query = f"""
    COPY (
        SELECT 
            A.kaptCode,
            CAST(P.전용면적 AS DOUBLE) AS 전용면적,
            MIN(TRY_CAST(REPLACE(P.공시가격, ',', '') AS BIGINT)) AS min_price,
            MAX(TRY_CAST(REPLACE(P.공시가격, ',', '') AS BIGINT)) AS max_price
        FROM read_csv_auto('{pub_price_file}', all_varchar=true) AS P
        INNER JOIN read_csv_auto('{apt_basic_file}', all_varchar=true) AS A
            ON P.법정동코드 = A.bjdCode
           AND REPLACE(P.도로명주소, ' ', '') = REPLACE(A.doroJuso, ' ', '')
        GROUP BY A.kaptCode, CAST(P.전용면적 AS DOUBLE)
    ) TO '{output_csv}' (HEADER, DELIMITER ',');
    """

    duckdb.sql(query)
    print(f'성공적으로 추출 및 저장이 완료되었습니다! ({output_csv})')

if __name__ == "__main__":
    process_price_data()
