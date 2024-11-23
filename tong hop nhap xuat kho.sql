WITH
    location_info AS (
        SELECT id
        FROM stock_location
        WHERE id = 28
    ),
    stock_move_ids AS (
        SELECT
            id AS move_id,
            product_id,
            location_id,
            location_dest_id,
            quantity_done,
            state,
            write_date
        FROM stock_move
        WHERE
            state = 'done' AND
            (location_id = 28 OR location_dest_id = 28)
    ),
    dau_ky AS (
        SELECT
            product_id,
            SUM(quantity_done) AS dau_ky_sum
        FROM stock_move_ids
        WHERE write_date < '20241101'
        GROUP BY product_id
    ),
    nhap AS (
        SELECT
            product_id,
            SUM(quantity_done) AS nhap_sum
        FROM stock_move_ids
        WHERE
            location_id = 28 AND
            write_date >= '20241101' AND write_date <= '20241122'
        GROUP BY product_id
    ),
    xuat AS (
        SELECT
            product_id,
            SUM(quantity_done) AS xuat_sum
        FROM stock_move_ids
        WHERE
            location_dest_id = 28 AND
            write_date >= '20241101' AND write_date <= '20241122'
        GROUP BY product_id
    )

SELECT
    lf.id AS location_id,
    dk.product_id,
    COALESCE(dk.dau_ky_sum, 0) AS dau_ky_sum,
    COALESCE(nh.nhap_sum, 0) AS nhap_sum,
    COALESCE(xu.xuat_sum, 0) AS xuat_sum
FROM location_info lf
LEFT JOIN dau_ky dk ON TRUE
LEFT JOIN nhap nh ON dk.product_id = nh.product_id
LEFT JOIN xuat xu ON dk.product_id = xu.product_id
ORDER BY location_id, dk.product_id; 
