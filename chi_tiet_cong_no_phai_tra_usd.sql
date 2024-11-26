/*
    Tính năng: Chi tiết công nợ phải trả USD
    Người tạo: Nguyễn Văn Đạt
    Ngày tạo: 22/11/2024
*/

DROP TABLE IF EXISTS public.function_chi_tiet_cong_no_phai_tra_usd;
CREATE OR REPLACE FUNCTION public.function_chi_tiet_cong_no_phai_tra_usd(
    p_date_from timestamp without time zone,
    p_date_to timestamp without time zone,
    p_company_id integer,
    p_account_id integer,
    p_partner_id integer,
    p_id integer
)
RETURNS TABLE(account_id integer, partner_id integer)
LANGUAGE 'plpgsql'
COST 100
VOLATILE PARALLEL UNSAFE
ROWS 1000
AS $BODY$
declare
    _p_user_id integer = 0;
begin
    -- Lấy dữ liệu người dùng
    select tar.create_uid into _p_user_id from alpha_report tar where id = p_id;

    delete from beta_report_line5 where create_uid=_p_user_id;

    WITH

    tmp_account_account AS (
        SELECT DISTINCT aml.account_id as account_id,
                        aml.partner_id as partner_id
        FROM account_move_line aml
        LEFT JOIN account_move am ON am.id = aml.move_id
        WHERE aml.parent_state = 'posted'
        AND p_account_id = aml.account_id
        AND p_partner_id = aml.partner_id
    ),
    
    tmp_dau_ky AS (
        SELECT tcc.account_id as account_id,
               tcc.partner_id as partner_id,
               (SELECT sum(
                CASE WHEN aml.debit = 0
                        THEN 0
                        ELSE    CASE WHEN aml.currency_id = 2
                                    THEN aml.amount_currency
                                    ELSE aml.amount_currency * (SELECT rate FROM get_currency_rate(aml.date, p_company_id))
                                END
                    END
                ) 
                FROM account_move_line as aml
                WHERE aml.account_id = tcc.account_id
                  AND aml.partner_id = tcc.partner_id
                  AND aml.date < p_date_from
                  AND aml.parent_state = 'posted') as end_debit_usd,
               (SELECT sum(
                    CASE WHEN aml.credit = 0
                        THEN 0
                        ELSE    CASE WHEN aml.currency_id = 2
                                    THEN aml.amount_currency * -1
                                    ELSE aml.amount_currency * -1 * (SELECT rate FROM get_currency_rate(aml.date, p_company_id))
                                END
                    END
               ) 
                FROM account_move_line as aml
                WHERE aml.account_id = tcc.account_id
                  AND aml.partner_id = tcc.partner_id
                  AND aml.date < p_date_from
                  AND aml.parent_state = 'posted') as end_credit_usd,
                (SELECT sum(
                    CASE WHEN aml.debit = 0
                        THEN 0
                        ELSE    CASE WHEN aml.currency_id = 23
                                    THEN aml.amount_currency
                                    ELSE aml.amount_currency / (SELECT rate FROM get_currency_rate(aml.date, p_company_id))
                                END
                    END
                )
                FROM account_move_line as aml
                WHERE aml.account_id = tcc.account_id
                  AND aml.partner_id = tcc.partner_id
                  AND aml.date < p_date_from
                  AND aml.parent_state = 'posted') as end_debit_vnd,
               (SELECT sum(
                    CASE WHEN aml.credit = 0
                        THEN 0
                        ELSE    CASE WHEN aml.currency_id = 23
                                    THEN aml.amount_currency * -1
                                    ELSE aml.amount_currency * -1 / (SELECT rate FROM get_currency_rate(aml.date, p_company_id))
                                END
                    END
                )
                FROM account_move_line as aml
                WHERE aml.account_id = tcc.account_id
                  AND aml.partner_id = tcc.partner_id
                  AND aml.date < p_date_from
                  AND aml.parent_state = 'posted') as end_credit_vnd
        FROM tmp_account_account tcc
    ),

    tmp_account AS (
        SELECT DISTINCT am.id as move_id
        FROM account_move_line aml
        LEFT JOIN account_move am ON aml.move_id = am.id
        WHERE aml.partner_id = p_partner_id
        AND aml.account_id = p_account_id
        AND am.state = 'posted' 
        AND am.move_type = 'in_invoice'
        AND (p_date_from <= am.invoice_date AND am.invoice_date <= p_date_to)
    ),

    tmp_one AS (
        SELECT aml.id as line_id, ta.move_id as move_id
        FROM account_move_line aml
        INNER JOIN tmp_account ta ON aml.move_id = ta.move_id
        WHERE p_account_id != aml.account_id
    ),

    tmp_two AS (
        SELECT apr.debit_move_id as line_id, ta.move_id as move_id
        FROM account_move_line aml
        INNER JOIN tmp_account ta ON aml.move_id = ta.move_id
        LEFT JOIN account_partial_reconcile apr ON apr.credit_move_id = aml.id
    ),

    tmp_one_two AS (
        SELECT line_id, move_id FROM tmp_one
        UNION
        SELECT line_id, move_id FROM tmp_two
    ),

    tmp_account_move_for_payment AS (
        SELECT DISTINCT am.id as move_id
        FROM account_move_line aml
        LEFT JOIN account_move am ON aml.move_id = am.id
        LEFT OUTER JOIN tmp_two tt ON aml.id = tt.line_id
        WHERE aml.partner_id = p_partner_id
        AND tt.line_id IS NULL
        AND aml.account_id = p_account_id
        AND am.state = 'posted' 
        AND am.move_type = 'entry'
        AND am.payment_id IS NOT NULL
        AND (p_date_from <= am.date AND am.date <= p_date_to)
    ),

    tmp_three AS (
        SELECT aml.id as line_id, ta.move_id as move_id
        FROM account_move_line aml
        INNER JOIN tmp_account_move_for_payment ta ON aml.move_id = ta.move_id
        WHERE p_account_id != aml.account_id
    ),

    tmp_account_move_line AS (
        SELECT line_id, move_id FROM tmp_one_two
        UNION
        SELECT line_id, move_id FROM tmp_three
    ),

    tmp_account_account2 AS (
        SELECT DISTINCT aml.move_id as move_id
        FROM account_move_line aml
        INNER JOIN tmp_account_move_line tal ON tal.line_id = aml.id
    ),

    tmp_phat_sinh_trong_ky AS (
        SELECT aml.partner_id as partner_id,
               rp.code_contact as partner_code,
               am.invoice_date as invoice_date,
               aml.date as date,
               aml.move_id as move_id,
               am.ref as reference,
               aml.quantity as product_uom_qty,
               aml.price_unit as price_unit,
               aml.name as note,
               aml.account_id as account_dest_id,
               (
                CASE WHEN aml.debit = 0
                    THEN 0
                    ELSE    CASE WHEN aml.currency_id = 2
                                THEN aml.amount_currency
                                ELSE aml.amount_currency * (SELECT rate FROM get_currency_rate(aml.date, p_company_id))
                            END
                END
                ) AS debit_usd,
                (
                    CASE WHEN aml.credit = 0
                        THEN 0
                        ELSE    CASE WHEN aml.currency_id = 2
                                    THEN aml.amount_currency * -1
                                    ELSE aml.amount_currency * -1 * (SELECT rate FROM get_currency_rate(aml.date, p_company_id))
                                END
                    END
                ) AS credit_usd,
                (
                    CASE WHEN aml.debit = 0
                        THEN 0
                        ELSE    CASE WHEN aml.currency_id = 23
                                    THEN aml.amount_currency
                                    ELSE aml.amount_currency / (SELECT rate FROM get_currency_rate(aml.date, p_company_id))
                                END
                    END
                ) AS debit_vnd,
                (
                    CASE WHEN aml.credit = 0
                        THEN 0
                        ELSE    CASE WHEN aml.currency_id = 23
                                    THEN aml.amount_currency * -1
                                    ELSE aml.amount_currency * -1 / (SELECT rate FROM get_currency_rate(aml.date, p_company_id))
                                END
                    END
                ) AS credit_vnd,
               aml.product_uom_id as uom_id
        FROM account_move_line aml
        LEFT JOIN account_move am ON am.id = aml.move_id
        INNER JOIN tmp_account_account2 taa ON taa.move_id = am.id
        LEFT JOIN res_partner rp ON rp.id = aml.partner_id
        WHERE p_account_id != aml.account_id
        AND p_partner_id = aml.partner_id
        AND am.state = 'posted'
        ORDER BY CASE
                     WHEN am.invoice_date IS NOT NULL THEN am.invoice_date
                     ELSE am.date
                 END, taa.move_id
    )

    -- Insert Số dư đầu kỳ and transactions (phát sinh trong kỳ)
    INSERT INTO public.beta_report_line5(
            parent_id, create_uid, write_uid,
            partner_id, invoice_date, date,
            move_id, reference, note,
            account_id, account_dest_id,
            ps_debit, ps_credit,
            ps_debit_nt, ps_credit_nt,
            end_debit, end_credit,
            end_debit_nt, end_credit_nt,
            product_uom_quantity, price_unit, uom_id
    )
    SELECT
        p_id, _p_user_id, _p_user_id,
        rs.partner_id, NULL::timestamp, NULL::timestamp,
        NULL::integer, NULL::varchar, 'Số dư đầu kỳ',
        NULL::integer, NULL::integer,
        0, 0,
        0, 0,
        rs.end_credit_vnd, rs.end_debit_vnd,
        rs.end_credit_usd, rs.end_debit_usd,
        NULL::numeric, NULL::numeric, NULL::integer
    FROM tmp_dau_ky rs

    UNION ALL

    SELECT
        p_id, _p_user_id, _p_user_id,
        rs.partner_id, rs.invoice_date, rs.date,
        rs.move_id, rs.reference, rs.note,
        p_account_id, rs.account_dest_id,
        rs.credit_vnd, rs.debit_vnd,
        rs.credit_usd, rs.debit_usd,
        0, 0,
        0, 0,
        rs.product_uom_qty, rs.price_unit, rs.uom_id
    FROM tmp_phat_sinh_trong_ky rs;


    -- Kết quả trả về
    RETURN QUERY
    SELECT p_account_id, p_partner_id;

end
$BODY$;
