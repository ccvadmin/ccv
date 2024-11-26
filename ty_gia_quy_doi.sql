/*
    Hàm: Lấy tỷ giá quy đổi
    Người tạo: Nguyễn Văn Đạt
    Ngày tạo: 26/11/2024
*/
DROP FUNCTION IF EXISTS public.get_currency_rate;
CREATE OR REPLACE FUNCTION public.get_currency_rate(date_currency DATE, p_company_id INT)
RETURNS TABLE(currency_id integer, rate numeric)
LANGUAGE 'plpgsql'
COST 100
VOLATILE PARALLEL UNSAFE
ROWS 1000
AS $BODY$
BEGIN
    RETURN QUERY
    SELECT c.id,
        COALESCE(
            (SELECT r.rate 
             FROM res_currency_rate r
             WHERE r.currency_id = c.id 
               AND r.name <= date_currency
               AND (r.company_id IS NULL OR r.company_id = p_company_id)
             ORDER BY r.company_id, r.name DESC
             LIMIT 1), 1.0
        ) AS rate
    FROM res_currency c
    WHERE c.id = 2;
END
$BODY$;
