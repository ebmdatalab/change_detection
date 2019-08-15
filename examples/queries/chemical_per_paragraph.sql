SELECT
  DISTINCT i.code,
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
    SUBSTR(bnf_code, 0, 6) AS code,
    month AS month,
    SUM(items) AS denominator
  FROM
    hscic.normalised_prescribing_standard
  GROUP BY
    code,
    month) AS s
ON
  SUBSTR(i.code, 0, 6) = s.code
  AND i.month = s.month
WHERE
  i.code IS NOT NULL
  AND denominator IS NOT NULL
ORDER BY
  i.code,
  month