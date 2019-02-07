SELECT
  DISTINCT code,
  i.month,
  numerator,
  denominator
FROM (
  SELECT
    SUBSTR(bnf_code, 0, 9) AS code,
    month,
    SUM(items) AS numerator
  FROM
    hscic.normalised_prescribing_standard
  GROUP BY
    code,
    month) AS i
LEFT JOIN (
  SELECT
    month,
    SUM(total_list_size) AS denominator
  FROM
    hscic.practice_statistics_all_years
  GROUP BY
    month) AS s
ON
  i.month = s.month
WHERE
  code IS NOT NULL
  AND denominator IS NOT NULL
ORDER BY
  code,
  month
--LIMIT
--  4000