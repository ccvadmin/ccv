/*
    Tính năng: Tổng hợp công nợ phải trả
    Người tạo: Nguyễn Văn Đạt
    Ngày tạo: 01/11/2024
    Lịch sử chỉnh sửa:
        - 02/11/2024 : Tạo mới
        - 05/11/2024 : Đổi tempory sang With
*/

DROP TABLE IF EXISTS report_tong_hop_cong_no_phai_tra;

DROP FUNCTION IF EXISTS public.function_tong_hop_cong_no_phai_tra_1_kh;
CREATE OR REPLACE FUNCTION public.function_tong_hop_cong_no_phai_tra_1_kh(
    p_date_from timestamp without time zone,
    p_date_to timestamp without time zone,
    p_account_id integer,
    p_partner_id integer,
    p_user_id integer,
    p_id integer
)
RETURNS TABLE(partner_id integer
            , account_id integer
            )
LANGUAGE 'plpgsql'
COST 100
VOLATILE PARALLEL UNSAFE
ROWS 1000

AS $BODY$
BEGIN
    -- Xóa dữ liệu
    delete from beta_report_line2 where parent_id = p_id;
    
    -- lấy dữ liệu tài khoản, khách hàng
    WITH account_partner AS (
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
               (SELECT SUM(aml.debit) FROM account_move_line aml
                WHERE aml.account_id = tcc.account_id
                  AND aml.partner_id = tcc.partner_id
                  AND aml.date < p_date_from
                  AND aml.parent_state = 'posted') AS start_debit,
               (SELECT SUM(aml.credit) FROM account_move_line aml
                WHERE aml.account_id = tcc.account_id
                  AND aml.partner_id = tcc.partner_id
                  AND aml.date < p_date_from
                  AND aml.parent_state = 'posted') AS start_credit
        FROM account_partner tcc
    ),

    -- lấy hóa đơn (in_invoice)
    invoice_in AS (
        SELECT DISTINCT am.id AS move_id
        FROM account_move_line aml
        LEFT JOIN account_move am ON aml.move_id = am.id
        WHERE aml.partner_id = p_partner_id
          AND aml.account_id = p_account_id
          AND am.state = 'posted'
          AND am.move_type = 'in_invoice'
          AND p_date_from <= am.invoice_date
          AND am.invoice_date <= p_date_to
    ),

    -- lấy move line hóa đơn
    move_line_invoice AS (
        SELECT aml.id AS line_id, ta.move_id
        FROM account_move_line aml
        INNER JOIN invoice_in ta ON aml.move_id = ta.move_id
        WHERE p_account_id != aml.account_id
    ),

    -- lấy move line thanh toán
    move_line_payment AS (
        SELECT apr.debit_move_id AS line_id, ta.move_id
        FROM account_move_line aml
        INNER JOIN invoice_in ta ON aml.move_id = ta.move_id
        LEFT JOIN account_partial_reconcile apr ON apr.credit_move_id = aml.id
    ),

    -- gộp move line hóa đơn và thanh toán
    move_line_invoice_payment AS (
        SELECT line_id, move_id FROM move_line_invoice
        UNION
        SELECT line_id, move_id FROM move_line_payment
    ),

    -- lấy các khoản trả trước không gắn vào hóa đơn
    account_paied_no_invoice AS (
        SELECT DISTINCT am.id AS move_id
        FROM account_move_line aml
        LEFT JOIN account_move am ON aml.move_id = am.id
        LEFT JOIN move_line_payment tt ON aml.id = tt.line_id
        WHERE aml.partner_id = p_partner_id
          AND tt.line_id IS NULL
          AND aml.account_id = p_account_id
          AND am.state = 'posted'
          AND am.move_type = 'entry'
          AND am.payment_id IS NOT NULL
          AND p_date_from <= am.date
          AND am.date <= p_date_to
    ),

    -- lấy move line của các khoản trả trước không gắn vào hóa đơn
    tmp_account_paied_no_invoice AS (
        SELECT aml.id AS line_id, ta.move_id
        FROM account_move_line aml
        INNER JOIN account_paied_no_invoice ta ON aml.move_id = ta.move_id
        WHERE p_account_id != aml.account_id
    ),

    -- gộp move line của hóa đơn và khoản trả trước
    tmp_account_move_line_invoice AS (
        SELECT line_id, move_id FROM move_line_invoice_payment
        UNION
        SELECT line_id, move_id FROM tmp_account_paied_no_invoice
    ),

    -- lấy các invoice để tính chi tiết hóa đơn bán ra
    account_partner2 AS (
        SELECT DISTINCT aml.move_id
        FROM account_move_line aml
        INNER JOIN tmp_account_move_line_invoice tal ON tal.line_id = aml.id
    ),

    -- tính chi tiết hóa đơn bán ra trong kỳ
    phat_sinh_trong_ky_khach_hang AS (
        SELECT aml.date AS date,
               aml.move_id,
               am.ref AS reference,
               aml.debit,
               aml.credit
        FROM account_move_line aml
        LEFT JOIN account_move am ON am.id = aml.move_id
        INNER JOIN account_partner2 taa ON taa.move_id = am.id
        WHERE p_account_id != aml.account_id
          AND p_partner_id = aml.partner_id
          AND am.state = 'posted'
        ORDER BY CASE WHEN am.invoice_date IS NOT NULL THEN am.invoice_date
                      ELSE am.date END, taa.move_id
    )

    -- Insert và trả về kết quả cuối cùng
    INSERT INTO beta_report_line2 (
        parent_id, create_uid, write_uid, -- bắt buộc
        partner_id, account_id, start_credit, start_debit, ps_credit, ps_debit
    )
    VALUES (
        p_id, p_user_id, p_user_id, -- bắt buộc
        p_partner_id,
        p_account_id,
        (SELECT sh.start_credit FROM so_du_dau_ky_khach_hang sh WHERE sh.partner_id = p_partner_id),
        (SELECT sh.start_debit FROM so_du_dau_ky_khach_hang sh WHERE sh.partner_id = p_partner_id),
        (SELECT SUM(ps.debit) FROM phat_sinh_trong_ky_khach_hang ps WHERE ps.move_id IN (SELECT move_id FROM phat_sinh_trong_ky_khach_hang)),
        (SELECT SUM(ps.credit) FROM phat_sinh_trong_ky_khach_hang ps WHERE ps.move_id IN (SELECT move_id FROM phat_sinh_trong_ky_khach_hang))
    );

    -- Kết quả trả về
    RETURN QUERY
    SELECT p_partner_id, p_account_id;
END
$BODY$;