/*
    Tính năng: Chi tiết công nợ phải thu USD
    Người tạo: Nguyễn Văn Đạt
    Ngày tạo: 23/11/2024
*/

CREATE OR REPLACE FUNCTION public.function_chi_tiet_cong_no_phai_thu_usd(
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
    --
    select tar.create_uid into _p_user_id from alpha_report tar where id = p_id;
    delete from beta_report_line6 where create_uid=_p_user_id;

    -- With clause for tmp_account
    WITH
	tong_hop_cong_no_currency AS (
        SELECT c.id,
            COALESCE((
                SELECT r.rate 
                FROM res_currency_rate r
                WHERE r.currency_id = c.id 
                AND r.name = (SELECT MAX(r2.name) 
                            FROM res_currency_rate r2 
                            WHERE r2.currency_id = r.currency_id 
                            AND (r2.company_id = p_company_id)) 
                AND (r.company_id IS NULL OR r.company_id = p_company_id)
                LIMIT 1
            ), 1.0) AS rate
        FROM res_currency c
        WHERE c.id = 2
        UNION
        SELECT c.id,
            COALESCE((
                SELECT r.rate 
                FROM res_currency_rate r
                WHERE r.currency_id = c.id 
                AND r.name = (SELECT MAX(r2.name) 
                            FROM res_currency_rate r2 
                            WHERE r2.currency_id = r.currency_id 
                            AND r2.company_id = p_company_id)
                AND (r.company_id IS NULL OR r.company_id = p_company_id)
                LIMIT 1
            ), 1.0) AS rate
        FROM res_currency c
        WHERE c.id = 23
    ),
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
                                    ELSE aml.amount_currency * thc_usd.rate
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
                                    ELSE aml.amount_currency * -1 * thc_usd.rate
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
                                    ELSE aml.amount_currency / thc_usd.rate
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
                                    ELSE aml.amount_currency * -1 / thc_usd.rate
                                END
                    END
                )
                FROM account_move_line as aml
                WHERE aml.account_id = tcc.account_id
                  AND aml.partner_id = tcc.partner_id
                  AND aml.date < p_date_from
                  AND aml.parent_state = 'posted') as end_credit_vnd
        FROM tmp_account_account tcc
        LEFT JOIN tong_hop_cong_no_currency thc_usd ON thc_usd.id = 2  -- USD rate
    ),
	tmp_account AS (
        select DISTINCT am.id as move_id
        from account_move_line aml
        left join account_move am on aml.move_id = am.id
        where aml.partner_id = p_partner_id
        and aml.account_id = p_account_id
        and am.state = 'posted' and am.move_type = 'out_invoice'
        and(p_date_from <= am.invoice_date and am.invoice_date <= p_date_to)
    ),
    
    -- With clause for tmp_one
    tmp_one AS (
        select aml.id as line_id, ta.move_id as move_id
        from account_move_line aml
        inner join tmp_account ta on aml.move_id = ta.move_id
        where p_account_id != aml.account_id
    ),
    
    -- With clause for tmp_two
    tmp_two AS (
        select apr.credit_move_id as line_id, ta.move_id as move_id
        from account_move_line aml
        inner join tmp_account ta on aml.move_id = ta.move_id
        left join account_partial_reconcile apr on apr.debit_move_id = aml.id
    ),
    
    -- With clause for tmp_one_two
    tmp_one_two AS (
        SELECT line_id as line_id, move_id as move_id FROM tmp_one
        UNION
        SELECT  line_id as line_id, move_id as move_id FROM tmp_two
    ),
    
    -- With clause for tmp_account_move_for_payment
    tmp_account_move_for_payment AS (
        select DISTINCT am.id as move_id
        from account_move_line aml
        left join account_move am on aml.move_id = am.id
        left outer join tmp_two tt on aml.id = tt.line_id
        where aml.partner_id = p_partner_id
        and tt.line_id is null
        and aml.account_id = p_account_id
        and am.state = 'posted' and am.move_type = 'entry'
        and am.payment_id is not null
        and(p_date_from <= am.date and am.date <= p_date_to)
    ),
    
    -- With clause for tmp_three
    tmp_three AS (
        select aml.id as line_id, ta.move_id as move_id
        from account_move_line aml
        inner join tmp_account_move_for_payment ta on aml.move_id = ta.move_id
        where p_account_id != aml.account_id
    ),
    
    -- With clause for tmp_account_move_line
    tmp_account_move_line AS (
        SELECT line_id as line_id, move_id as move_id FROM tmp_one_two
        UNION
        SELECT  line_id as line_id, move_id as move_id FROM tmp_three
    ),
    
    -- With clause for tmp_account_move
    tmp_account_move AS (
        SELECT DISTINCT aml.move_id as move_id, rs.move_id as move_origin_id
        from account_move_line aml
        inner join tmp_account_move_line rs on rs.line_id = aml.id
    ),
    
    -- With clause for tmp_phat_sinh_trong_ky
    tmp_phat_sinh_trong_ky AS (
        select
            aml.partner_id as partner_id
            , am.date
			, am.invoice_date
            , tam.move_origin_id as move_id
            -- , vs.name as reference
            , '' as reference
            , aml.quantity as product_uom_qty
            , aml.price_unit as price_unit
            , (
				CASE WHEN aml.debit = 0
					THEN aml.name
					ELSE 
						CASE WHEN product_id is NULL
							THEN aml.name
						ELSE (SELECT CONCAT('[', pp.default_code, '] ', pt.name->>'vi_VN') FROM product_product pp JOIN product_template pt ON pp.product_tmpl_id = pt.id WHERE pp.id = aml.product_id)
					END
				END
			) AS note
			, (
				CASE WHEN aml.debit = 0
					THEN 0
					ELSE    CASE WHEN aml.currency_id = 2
								THEN aml.amount_currency
								ELSE aml.amount_currency * thc_usd.rate
							END
				END
			) AS debit_usd
			, (
				CASE WHEN aml.credit = 0
					THEN 0
					ELSE    CASE WHEN aml.currency_id = 2
								THEN aml.amount_currency * -1
								ELSE aml.amount_currency * -1 * thc_usd.rate
							END
				END
			) AS credit_usd
			, (
				CASE WHEN aml.debit = 0
					THEN 0
					ELSE    CASE WHEN aml.currency_id = 23
								THEN aml.amount_currency
								ELSE aml.amount_currency / thc_usd.rate
							END
				END
			) AS debit_vnd
			, (
				CASE WHEN aml.credit = 0
					THEN 0
					ELSE    CASE WHEN aml.currency_id = 23
								THEN aml.amount_currency * -1
								ELSE aml.amount_currency * -1 / thc_usd.rate
							END
				END
			) AS credit_vnd
            , aml.account_id as account_dest_id
            , aml.product_uom_id as uom_id
            , pp.id as product_id
        from account_move_line aml
        left join product_product pp on pp.id = aml.product_id
        left join account_move am on am.id = aml.move_id
        inner join tmp_account_move tam on tam.move_id = am.id
        -- left join viettel_sinvoice vs on vs.invoice_id = am.id
        LEFT JOIN tong_hop_cong_no_currency thc_usd ON thc_usd.id = 2  -- USD rate
        where
            p_account_id != aml.account_id
            and p_partner_id = aml.partner_id
            and am.state = 'posted'
        ORDER BY case
            when am.invoice_date is not null then am.invoice_date
            else am.date
            end, tam.move_origin_id, pp.id
    )

    -- Insert dữ liệu phát sinh trong kỳ
    insert into beta_report_line6(
        parent_id, create_uid, write_uid -- bắt buộc
        , partner_id, date, invoice_date
        , move_id, reference, note
        , account_id, account_dest_id
        , ps_debit, ps_credit
        , ps_debit_nt, ps_credit_nt
		, end_debit, end_credit
        , end_debit_nt, end_credit_nt
        , product_uom_quantity, price_unit, uom_id
		, product_id
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
        NULL::numeric, NULL::numeric, NULL::integer,
		NULL::integer
    FROM tmp_dau_ky rs
    UNION ALL
    select
         p_id , _p_user_id, _p_user_id
        , rs.partner_id, rs.date, rs.invoice_date
        , rs.move_id, rs.reference, rs.note
        , p_account_id, rs.account_dest_id
        , rs.credit_vnd, rs.debit_vnd
        , rs.credit_usd, rs.debit_usd
		, 0 , 0
        , 0 , 0
        , rs.product_uom_qty, rs.price_unit, rs.uom_id
		, rs.product_id
    from tmp_phat_sinh_trong_ky rs;

    -- Kết quả trả về
    return query
    select p_account_id, p_partner_id;
end
$BODY$;