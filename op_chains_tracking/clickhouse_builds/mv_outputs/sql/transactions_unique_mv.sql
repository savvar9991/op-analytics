CREATE MATERIALIZED VIEW IF NOT EXISTS lisk_transactions_unique_mv
ENGINE = ReplacingMergeTree(insert_time)
PARTITION BY toDate(block_timestamp)
ORDER BY (chain_id, hash, block_number, block_timestamp)
AS

-- Native Transactions
SELECT
        t.*

        , if(gas_price > 0, (cast((gas_price * t.receipt_gas_used) + receipt_l1_fee AS Nullable(Float64)))/1e18, 0) AS gas_fee_eth

        , ((length(unhex(input)) - 1)) AS input_byte_length
        , @num_zero_bytes_sql@ AS input_num_zero_bytes
        , @num_nonzero_bytes_sql@ AS input_num_nonzero_bytes
        , (receipt_l1_fee /
(
 16*COALESCE(receipt_l1_fee_scalar,receipt_l1_base_fee_scalar)*cast(receipt_l1_gas_price AS Nullable(Float64))/1e6
 + COALESCE( receipt_l1_blob_base_fee_scalar*cast(receipt_l1_blob_base_fee AS Nullable(Float64))/1e6 , 0)
)) AS estimated_size

        , if(gas_price > 0, CAST(receipt_l1_fee AS Nullable(Float64)) / 1e18, 0) AS l1_contrib_l2_eth_fees
        , if(gas_price > 0, CAST(gas_price * t.receipt_gas_used AS Nullable(Float64)) / 1e18, 0) AS l2_contrib_l2_eth_fees

        , if(gas_price > 0, (cast((receipt_l1_fee /
(
 16*COALESCE(receipt_l1_fee_scalar,receipt_l1_base_fee_scalar)*cast(receipt_l1_gas_price AS Nullable(Float64))/1e6
 + COALESCE( receipt_l1_blob_base_fee_scalar*cast(receipt_l1_blob_base_fee AS Nullable(Float64))/1e6 , 0)
)) as Nullable(Float64)) * COALESCE(16*receipt_l1_base_fee_scalar/1e6,receipt_l1_fee_scalar) * cast(receipt_l1_gas_price AS Nullable(Float64))) / 1e18, 0) AS l1_l1gas_contrib_l2_eth_fees
        , if(gas_price > 0, (cast((receipt_l1_fee /
(
 16*COALESCE(receipt_l1_fee_scalar,receipt_l1_base_fee_scalar)*cast(receipt_l1_gas_price AS Nullable(Float64))/1e6
 + COALESCE( receipt_l1_blob_base_fee_scalar*cast(receipt_l1_blob_base_fee AS Nullable(Float64))/1e6 , 0)
)) as Nullable(Float64)) * receipt_l1_blob_base_fee_scalar/1e6 * cast(receipt_l1_blob_base_fee AS Nullable(Float64))) / 1e18, 0) AS l1_blobgas_contrib_l2_eth_fees

FROM lisk_transactions t
WHERE t.is_deleted = 0
