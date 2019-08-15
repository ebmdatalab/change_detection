SELECT
  DATE(month) as month,
  practice AS code,
  SUM(IF(SUBSTR(bnf_code,1,11)='0703021Q0BB',
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
  bnf_code LIKE '0703021Q0%'
  AND
  month < "2016-01-01"
  AND
  (practice = 'D82621' OR practice = 'D83049' OR practice = 'H82006')
GROUP BY
  practice,
  month
ORDER BY
  practice,
  month