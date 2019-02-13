SELECT
  month,
  practice AS code,
  SUM(IF(SUBSTR(bnf_code,1,9)='0501080W0',
      items,
      0)) AS numerator,
  SUM(items) AS denominator
FROM
  ebmdatalab.hscic.normalised_prescribing_standard
INNER JOIN
  ebmdatalab.hscic.practices prac
ON
  practice = prac.code
  AND setting = 4
WHERE
  (bnf_code LIKE '0501130R0%'
  OR bnf_code LIKE '0501080W0%')
  AND
  month >= "2013-06-01"
  AND
  month <= "2018-06-01"
GROUP BY
  pct,
  practice,
  month
ORDER BY
  practice,
  month