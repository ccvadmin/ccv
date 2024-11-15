/*
    Tính năng: Tổng hợp công nợ phải thu
    Người tạo: Nguyễn Văn Đạt
    Ngày tạo: 02/11/2024
    Lịch sử chỉnh sửa:
        - 02/11/2024 : Tạo mới
        - 05/11/2024 : Đổi tempory sang With
        - 13/11/2024 : Thêm điều kiện không tạo khi không có giá trị
*/

DROP TABLE IF EXISTS report_tong_hop_cong_no_phai_thu;
DROP FUNCTION IF EXISTS function_tong_hop_cong_no_phai_thu_1_kh;
CREATE OR REPLACE FUNCTION public.function_tong_hop_cong_no_phai_thu_1_kh(
    p_date_from timestamp without time zone,
    p_date_to timestamp without time zone,
    p_account_id integer,
    p_partner_id integer,
    p_user_id integer,
    p_id integer
)
RETURNS TABLE(partner_id integer,
              account_id integer)
LANGUAGE 'plpgsql'
COST 100
VOLATILE PARALLEL UNSAFE
ROWS 1000
AS $BODY$
DECLARE
    sum_start_credit DECIMAL;
    sum_start_debit DECIMAL;
    sum_ps_debit DECIMAL;
    sum_ps_credit DECIMAL;
BEGIN
    -- Sử dụng WITH để thay thế các bảng tạm
    WITH 
    -- lấy dữ liệu tài khoản, khách hàng
    account_partner AS (
        SELECT DISTINCT aml.account_id, aml.partner_id
        FROM account_move_line aml
        LEFT JOIN account_move am ON am.id = aml.move_id
        WHERE aml.parent_state = 'posted'
          AND p_account_id = aml.account_id
          AND p_partner_id = aml.partner_id
    ),
    
    -- tính nợ có đầu kỳ
    so_du_dau_ky_khach_hang AS (
        SELECT tcc.account_id,
               tcc.partner_id,
               (SELECT SUM(aml.debit)
                FROM account_move_line aml
                WHERE aml.account_id = tcc.account_id
                  AND aml.partner_id = tcc.partner_id
                  AND aml.date < p_date_from
                  AND aml.parent_state = 'posted') AS start_debit,
               (SELECT SUM(aml.credit)
                FROM account_move_line aml
                WHERE aml.account_id = tcc.account_id
                  AND aml.partner_id = tcc.partner_id
                  AND aml.date < p_date_from
                  AND aml.parent_state = 'posted') AS start_credit
        FROM account_partner tcc
    ),
    
    -- lấy hoa đơn: out_invoice
    invoice_out AS (
        SELECT DISTINCT am.id AS move_id
        FROM account_move_line aml
        LEFT JOIN account_move am ON aml.move_id = am.id
        WHERE aml.partner_id = p_partner_id
          AND aml.account_id = p_account_id
          AND am.state = 'posted'
          AND am.move_type = 'out_invoice'
          AND p_date_from <= am.invoice_date AND am.invoice_date <= p_date_to
    ),
    
    -- Move line hoa đơn
    move_line_invoice AS (
        SELECT aml.id AS line_id, ta.move_id
        FROM account_move_line aml
        INNER JOIN invoice_out ta ON aml.move_id = ta.move_id
        WHERE p_account_id != aml.account_id
    ),
    
    -- Move line thanh toán (do phải thu nên search bằng debit lấy credit)
    move_line_payment AS (
        SELECT apr.credit_move_id AS line_id, ta.move_id
        FROM account_move_line aml
        INNER JOIN invoice_out ta ON aml.move_id = ta.move_id
        LEFT JOIN account_partial_reconcile apr ON apr.debit_move_id = aml.id
    ),
    
    -- Gộp 2 bảng lại
    move_lime_invoice_payment AS (
        SELECT line_id, move_id FROM move_line_invoice
        UNION
        SELECT line_id, move_id FROM move_line_payment
    ),
    
    -- lấy luôn các khoản trả trước không gắn vào hóa đơn
    account_paied_no_invoice AS (
        SELECT DISTINCT am.id AS move_id
        FROM account_move_line aml
        LEFT JOIN account_move am ON aml.move_id = am.id
        LEFT OUTER JOIN move_line_payment tt ON aml.id = tt.line_id
        WHERE aml.partner_id = p_partner_id
          AND tt.line_id IS NULL
          AND aml.account_id = p_account_id
          AND am.state = 'posted'
          AND am.move_type = 'entry'
          AND am.payment_id IS NOT NULL
          AND p_date_from <= am.date AND am.date <= p_date_to
    ),
    
    -- Xử lý các khoản trả trước không gắn hóa đơn
    tmp_account_paied_no_invoice AS (
        SELECT aml.id AS line_id, ta.move_id
        FROM account_move_line aml
        INNER JOIN account_paied_no_invoice ta ON aml.move_id = ta.move_id
        WHERE p_account_id != aml.account_id
    ),
    
    -- Gộp tất cả lại
    tmp_account_move_line_invoice AS (
        SELECT line_id, move_id FROM move_lime_invoice_payment
        UNION
        SELECT line_id, move_id FROM tmp_account_paied_no_invoice
    ),
    
    -- Lấy hóa đơn tổng bảng line tổng hợp
    tmp_account_move AS (
        SELECT DISTINCT aml.move_id, rs.move_id AS move_origin_id
        FROM account_move_line aml
        INNER JOIN tmp_account_move_line_invoice rs ON rs.line_id = aml.id
    ),
    
    -- Tính chi tiết hóa đơn bán ra trong kỳ
    phat_sinh_trong_ky_khach_hang AS (
        SELECT 
            CASE
                WHEN am.invoice_date IS NOT NULL THEN am.invoice_date
                ELSE am.date
            END AS date,
            tam.move_origin_id AS move_id,
            aml.debit AS debit,
            aml.credit AS credit
        FROM account_move_line aml
        LEFT JOIN account_move am ON am.id = aml.move_id
        INNER JOIN tmp_account_move tam ON tam.move_id = am.id
        LEFT JOIN viettel_sinvoice vs ON vs.invoice_id = am.id
        WHERE p_account_id != aml.account_id
          AND p_partner_id = aml.partner_id
          AND am.state = 'posted'
        ORDER BY CASE
                   WHEN am.invoice_date IS NOT NULL THEN am.invoice_date
                   ELSE am.date
                 END, tam.move_origin_id
    )

    SELECT
        (SELECT dk.start_credit FROM so_du_dau_ky_khach_hang dk WHERE dk.partner_id = p_partner_id LIMIT 1) AS start_credit_val,
        (SELECT dk.start_debit FROM so_du_dau_ky_khach_hang dk WHERE dk.partner_id = p_partner_id LIMIT 1) AS start_debit_val,
        (SELECT SUM(ps.debit) FROM phat_sinh_trong_ky_khach_hang ps LIMIT 1) AS total_debit_val,
        (SELECT SUM(ps.credit) FROM phat_sinh_trong_ky_khach_hang ps LIMIT 1) AS total_credit_val
    INTO sum_start_credit, sum_start_debit, sum_ps_debit, sum_ps_credit;

    -- Thêm Partner đã hoàn thành tính toán vào bảng
    IF sum_start_credit != 0 OR sum_start_debit != 0 OR sum_ps_debit != 0 OR sum_ps_credit != 0 THEN
            INSERT INTO beta_report_line1 (
                parent_id, create_uid, write_uid, -- bắt buộc
                partner_id, account_id, start_credit, start_debit, ps_credit, ps_debit
            )
            VALUES ( 
                p_id, p_user_id, p_user_id, -- bắt buộc
                p_partner_id, p_account_id, sum_start_credit, sum_start_debit, sum_ps_debit, sum_ps_credit
            );
    END IF;

    -- Kết quả trả về
    RETURN QUERY 
    SELECT p_partner_id, p_account_id;
END;
$BODY$;