param(
  [string]$SourcePath = "C:\Users\beher\Downloads\odia_calendar_2026.txt"
)

$ErrorActionPreference = "Stop"
$BaseDir = if ($PSScriptRoot) { $PSScriptRoot } else { Join-Path (Get-Location).Path "calendar_overrides" }

$monthMap = [ordered]@{
  January = "01"
  February = "02"
  March = "03"
  April = "04"
  May = "05"
  June = "06"
  July = "07"
  August = "08"
  September = "09"
  October = "10"
  November = "11"
  December = "12"
}

$oriyaDigits = @{
  "୦" = "0"; "୧" = "1"; "୨" = "2"; "୩" = "3"; "୪" = "4"
  "୫" = "5"; "୬" = "6"; "୭" = "7"; "୮" = "8"; "୯" = "9"
}

$odiaToDevanagari = @{
  "ଁ"="ँ"; "ଂ"="ं"; "ଃ"="ः"; "ଅ"="अ"; "ଆ"="आ"; "ଇ"="इ"; "ଈ"="ई"; "ଉ"="उ"; "ଊ"="ऊ"
  "ଋ"="ऋ"; "ଌ"="ऌ"; "ଏ"="ए"; "ଐ"="ऐ"; "ଓ"="ओ"; "ଔ"="औ"; "ା"="ा"; "ି"="ि"; "ୀ"="ी"
  "ୁ"="ु"; "ୂ"="ू"; "ୃ"="ृ"; "ୄ"="ॄ"; "େ"="े"; "ୈ"="ै"; "ୋ"="ो"; "ୌ"="ौ"; "୍"="्"
  "କ"="क"; "ଖ"="ख"; "ଗ"="ग"; "ଘ"="घ"; "ଙ"="ङ"; "ଚ"="च"; "ଛ"="छ"; "ଜ"="ज"; "ଝ"="झ"
  "ଞ"="ञ"; "ଟ"="ट"; "ଠ"="ठ"; "ଡ"="ड"; "ଢ"="ढ"; "ଣ"="ण"; "ତ"="त"; "ଥ"="थ"; "ଦ"="द"
  "ଧ"="ध"; "ନ"="न"; "ପ"="प"; "ଫ"="फ"; "ବ"="ब"; "ଭ"="भ"; "ମ"="म"; "ଯ"="य"; "ୟ"="य"
  "ର"="र"; "ଲ"="ल"; "ଳ"="ळ"; "ଵ"="व"; "ଶ"="श"; "ଷ"="ष"; "ସ"="स"; "ହ"="ह"; "ଡ଼"="ड़"
  "ଢ଼"="ढ़"; "ୱ"="व"; "ୠ"="ॠ"; "ୡ"="ॡ"; "୦"="0"; "୧"="1"; "୨"="2"; "୩"="3"; "୪"="4"
  "୫"="5"; "୬"="6"; "୭"="7"; "୮"="8"; "୯"="9"; "’"="'"
}

$latinVowels = @{
  "ଅ"="a"; "ଆ"="aa"; "ଇ"="i"; "ଈ"="ii"; "ଉ"="u"; "ଊ"="uu"; "ଋ"="ri"; "ଌ"="li"
  "ଏ"="e"; "ଐ"="ai"; "ଓ"="o"; "ଔ"="au"
}

$latinMatras = @{
  "ା"="aa"; "ି"="i"; "ୀ"="ii"; "ୁ"="u"; "ୂ"="uu"; "ୃ"="ri"; "େ"="e"; "ୈ"="ai"; "ୋ"="o"; "ୌ"="au"
}

$latinConsonants = @{
  "କ"="k"; "ଖ"="kh"; "ଗ"="g"; "ଘ"="gh"; "ଙ"="ng"; "ଚ"="ch"; "ଛ"="chh"; "ଜ"="j"; "ଝ"="jh"
  "ଞ"="ny"; "ଟ"="t"; "ଠ"="th"; "ଡ"="d"; "ଢ"="dh"; "ଣ"="n"; "ତ"="t"; "ଥ"="th"; "ଦ"="d"
  "ଧ"="dh"; "ନ"="n"; "ପ"="p"; "ଫ"="ph"; "ବ"="b"; "ଭ"="bh"; "ମ"="m"; "ଯ"="y"; "ୟ"="y"
  "ର"="r"; "ଲ"="l"; "ଳ"="l"; "ଵ"="v"; "ଶ"="sh"; "ଷ"="sh"; "ସ"="s"; "ହ"="h"; "ଡ଼"="d"
  "ଢ଼"="dh"; "ୱ"="v"
}

$englishExact = @{
  "ଇଂରାଜୀ ନୂତନ ବର୍ଷ ସନ ୨୦୨୭ ମସିହା ଆରମ୍ଭ" = "New Year's Day"
  "୭୭ତମ ସାଧାରଣତନ୍ତ୍ର ଦିବସ" = "77th Republic Day"
  "୮୦ ତମ ସ୍ୱାଧୀନତା ଦିବସ" = "80th Independence Day"
  "ଉତ୍କଳ ଦିବସ" = "Utkala Dibasa"
  "ଗୁଡ୍ ଫ୍ରାଇଡେ" = "Good Friday"
  "ଶ୍ରମିକ ଦିବସ" = "Labour Day"
  "ବୁଦ୍ଧ ଜୟନ୍ତୀ" = "Buddha Jayanti"
  "ଇଦ୍-ଉଲ୍-ଫିତର" = "Eid-ul-Fitr"
  "ଇଦ୍-ଉଲ୍-ଜୁହା" = "Eid-ul-Zuha"
  "ମହରମ୍" = "Muharram"
  "ମହାପୁରୁଷ ମହମ୍ମଦଙ୍କ ଜନ୍ମ ଦିବସ" = "Prophet Muhammad's Birthday"
  "ଗୁରୁ ଦିବସ" = "Teachers' Day"
  "ଗାନ୍ଧୀ ଜୟନ୍ତୀ" = "Gandhi Jayanti"
  "ଶାସ୍ତ୍ରୀ ଜୟନ୍ତୀ" = "Shastri Jayanti"
  "ଦୀପାବଳୀ" = "Diwali"
  "ଯୀଶୁଖ୍ରୀଷ୍ଟଙ୍କ ଜନ୍ମ (ବଡ଼ଦିନ)" = "Christmas Day"
  "ଇଂରାଜୀ ବର୍ଷ ଶେଷ" = "Year End"
}

$hindiExact = @{
  "ଇଂରାଜୀ ନୂତନ ବର୍ଷ ସନ ୨୦୨୭ ମସିହା ଆରମ୍ଭ" = "नव वर्ष दिवस"
  "୭୭ତମ ସାଧାରଣତନ୍ତ୍ର ଦିବସ" = "77वां गणतंत्र दिवस"
  "୮୦ ତମ ସ୍ୱାଧୀନତା ଦିବସ" = "80वां स्वतंत्रता दिवस"
  "ଉତ୍କଳ ଦିବସ" = "उत्कल दिवस"
  "ଗୁଡ୍ ଫ୍ରାଇଡେ" = "गुड फ्राइडे"
  "ଶ୍ରମିକ ଦିବସ" = "श्रमिक दिवस"
  "ବୁଦ୍ଧ ଜୟନ୍ତୀ" = "बुद्ध जयंती"
  "ଇଦ୍-ଉଲ୍-ଫିତର" = "ईद-उल-फितर"
  "ଇଦ୍-ଉଲ୍-ଜୁହା" = "ईद-उल-जुहा"
  "ମହରମ୍" = "मुहर्रम"
  "ମହାପୁରୁଷ ମହମ୍ମଦଙ୍କ ଜନ୍ମ ଦିବସ" = "हजरत मोहम्मद जयंती"
  "ଗୁରୁ ଦିବସ" = "शिक्षक दिवस"
  "ଗାନ୍ଧୀ ଜୟନ୍ତୀ" = "गांधी जयंती"
  "ଶାସ୍ତ୍ରୀ ଜୟନ୍ତୀ" = "शास्त्री जयंती"
  "ଦୀପାବଳୀ" = "दीपावली"
  "ଯୀଶୁଖ୍ରୀଷ୍ଟଙ୍କ ଜନ୍ମ (ବଡ଼ଦିନ)" = "क्रिसमस दिवस"
  "ଇଂରାଜୀ ବର୍ଷ ଶେଷ" = "वर्षांत"
}

$odiaExact = @{
  "ଇଂରାଜୀ ନୂତନ ବର୍ଷ ସନ ୨୦୨୭ ମସିହା ଆରମ୍ଭ" = "ଇଂରାଜୀ ନୂତନ ବର୍ଷ"
}

$odiaTypeMap = @{
  "awareness day" = "ଜାଗରୁକତା ଦିବସ"
  "awareness week" = "ଜାଗରୁକତା ସପ୍ତାହ"
  "awareness month" = "ଜାଗରୁକତା ମାସ"
  "public holiday" = "ସାର୍ବଜନିକ ଛୁଟି"
  "festival" = "ପର୍ବ"
}

$hindiTypeMap = @{
  "awareness day" = "जागरूकता दिवस"
  "awareness week" = "जागरूकता सप्ताह"
  "awareness month" = "जागरूकता महीना"
  "public holiday" = "सार्वजनिक अवकाश"
  "festival" = "त्योहार"
}

function Convert-OriyaDigits([string]$value) {
  return (($value.ToCharArray() | ForEach-Object {
    $char = [string]$_
    if ($oriyaDigits.ContainsKey($char)) { $oriyaDigits[$char] } else { $char }
  }) -join "")
}

function Split-TopLevel([string]$value, [string]$delimiterPattern) {
  $parts = New-Object System.Collections.Generic.List[string]
  $buffer = ""
  $depth = 0
  foreach ($char in $value.ToCharArray()) {
    if ($char -eq "(") { $depth++ }
    elseif ($char -eq ")" -and $depth -gt 0) { $depth-- }

    if ($depth -eq 0 -and ([string]$char) -match $delimiterPattern) {
      if ($buffer.Trim()) { [void]$parts.Add($buffer.Trim()) }
      $buffer = ""
      continue
    }

    $buffer += $char
  }

  if ($buffer.Trim()) { [void]$parts.Add($buffer.Trim()) }
  return $parts
}

function Split-CommaTopLevel([string]$value) {
  $parts = New-Object System.Collections.Generic.List[string]
  $buffer = ""
  $depth = 0
  foreach ($char in $value.ToCharArray()) {
    if ($char -eq "(") { $depth++ }
    elseif ($char -eq ")" -and $depth -gt 0) { $depth-- }

    if ($char -eq "," -and $depth -eq 0) {
      if ($buffer.Trim()) { [void]$parts.Add($buffer.Trim()) }
      $buffer = ""
      continue
    }

    $buffer += $char
  }

  if ($buffer.Trim()) { [void]$parts.Add($buffer.Trim()) }
  return $parts
}

function Expand-AtomicEvents([string]$item) {
  $item = $item.Trim()

  switch ($item) {
    "IBS Awareness Month & Stress Awareness Month (Starts)" { return @("IBS Awareness Month (Starts)", "Stress Awareness Month (Starts)") }
    "ନେତାଜୀ ଓ ବୀର ସୁରେନ୍ଦ୍ର ସାଏ ଜୟନ୍ତୀ" { return @("ନେତାଜୀ ଜୟନ୍ତୀ", "ବୀର ସୁରେନ୍ଦ୍ର ସାଏ ଜୟନ୍ତୀ") }
    "ଗାନ୍ଧୀ ଓ ଶାସ୍ତ୍ରୀ ଜୟନ୍ତୀ" { return @("ଗାନ୍ଧୀ ଜୟନ୍ତୀ", "ଶାସ୍ତ୍ରୀ ଜୟନ୍ତୀ") }
    "ପୂଷ୍ୟାଭିଷେକ ଓ ରାଜାଭିଷେକ" { return @("ପୂଷ୍ୟାଭିଷେକ", "ରାଜାଭିଷେକ") }
    "ଶିବ ଚତୁର୍ଦ୍ଦଶୀ ଉପବାସ ଓ ବେଢ଼ାପରିକ୍ରମା" { return @("ଶିବ ଚତୁର୍ଦ୍ଦଶୀ ଉପବାସ", "ବେଢ଼ାପରିକ୍ରମା") }
    "ଶିବ ଚତୁର୍ଦ୍ଦଶୀ ଓ ବେଢ଼ା ପରିକ୍ରମା" { return @("ଶିବ ଚତୁର୍ଦ୍ଦଶୀ", "ବେଢ଼ା ପରିକ୍ରମା") }
    "World Food Day / Spine Day" { return @("World Food Day", "Spine Day") }
    "World Stroke Day / World Psoriasis Day" { return @("World Stroke Day", "World Psoriasis Day") }
    "Pancreatic/Lung/Stomach/Prostate Cancer Awareness Month (Starts)" {
      return @(
        "Pancreatic Cancer Awareness Month (Starts)",
        "Lung Cancer Awareness Month (Starts)",
        "Stomach Cancer Awareness Month (Starts)",
        "Prostate Cancer Awareness Month (Starts)"
      )
    }
    default {
      if ($item -match " / ") { return $item -split " / " }
      return @($item)
    }
  }
}

function Convert-OdiaToDevanagari([string]$value) {
  $output = New-Object System.Text.StringBuilder
  foreach ($char in $value.ToCharArray()) {
    $key = [string]$char
    if ($odiaToDevanagari.ContainsKey($key)) {
      [void]$output.Append($odiaToDevanagari[$key])
    }
    else {
      [void]$output.Append($key)
    }
  }
  return $output.ToString()
}

function Convert-OdiaToLatin([string]$value) {
  $chars = $value.ToCharArray()
  $output = New-Object System.Text.StringBuilder
  for ($i = 0; $i -lt $chars.Length; $i++) {
    $char = [string]$chars[$i]
    if ($latinVowels.ContainsKey($char)) {
      [void]$output.Append($latinVowels[$char])
      continue
    }

    if ($latinConsonants.ContainsKey($char)) {
      $base = $latinConsonants[$char]
      $next = if ($i + 1 -lt $chars.Length) { [string]$chars[$i + 1] } else { "" }
      if ($latinMatras.ContainsKey($next)) {
        [void]$output.Append($base + $latinMatras[$next])
        $i++
      }
      elseif ($next -eq "୍") {
        [void]$output.Append($base)
        $i++
      }
      else {
        [void]$output.Append($base + "a")
      }
      continue
    }

    switch ($char) {
      "ଂ" { [void]$output.Append("m") }
      "ଁ" { [void]$output.Append("n") }
      "ଃ" { [void]$output.Append("h") }
      " " { [void]$output.Append(" ") }
      "(" { [void]$output.Append("(") }
      ")" { [void]$output.Append(")") }
      "-" { [void]$output.Append("-") }
      "'" { [void]$output.Append("'") }
      "’" { [void]$output.Append("'") }
      "଼" { }
      "‌" { }
      "‍" { }
      "“" { [void]$output.Append([char]34) }
      "”" { [void]$output.Append([char]34) }
      default {
        if ($oriyaDigits.ContainsKey($char)) {
          [void]$output.Append($oriyaDigits[$char])
        }
        else {
          [void]$output.Append($char)
        }
      }
    }
  }

  $result = $output.ToString()
  $replacements = [ordered]@{
    "dibasa" = "Day"
    "jayanti" = "Jayanti"
    "puja" = "Puja"
    "purnima" = "Purnima"
    "amabasya" = "Amavasya"
    "ekadashi" = "Ekadashi"
    "sankranti" = "Sankranti"
    "mela" = "Mela"
    "vrata" = "Vrat"
    "vrat" = "Vrat"
    "yatra" = "Yatra"
    "utsaba" = "Festival"
    "utsava" = "Festival"
    "arambha" = "Begins"
    "janma" = "Birth"
    "janmotsaba" = "Birth Festival"
    "panchami" = "Panchami"
    "sasthi" = "Shashthi"
    "ashtami" = "Ashtami"
    "navami" = "Navami"
    "chaturthi" = "Chaturthi"
    "chaturdashi" = "Chaturdashi"
    "mahotsava" = "Mahotsava"
    "mahodaya" = "Mahodaya"
    "mahodadhi" = "Mahodadhi"
    "snana" = "Snana"
    "masa" = "Month"
  }

  foreach ($key in $replacements.Keys) {
    $result = [regex]::Replace($result, "(?i)\b$key\b", $replacements[$key])
  }

  $result = $result -replace "\s+", " "
  return (Get-Culture).TextInfo.ToTitleCase($result.Trim().ToLowerInvariant())
}

function Get-EnglishName([string]$name) {
  if ($englishExact.ContainsKey($name)) { return $englishExact[$name] }
  if ($name -match "[A-Za-z]") {
    $clean = $name -replace " \(Starts\)", ""
    return $clean
  }
  return (Convert-OdiaToLatin $name)
}

function Get-HindiName([string]$name) {
  if ($hindiExact.ContainsKey($name)) { return $hindiExact[$name] }
  if ($name -match "[A-Za-z]") { return $name -replace " \(Starts\)", "" }
  return (Convert-OdiaToDevanagari $name)
}

function Get-OdiaName([string]$name) {
  if ($odiaExact.ContainsKey($name)) { return $odiaExact[$name] }
  return $name
}

function Get-EventType([string]$englishName) {
  if ($englishName -in @(
    "New Year's Day", "77th Republic Day", "Good Friday", "Labour Day", "80th Independence Day",
    "Gandhi Jayanti", "Shastri Jayanti", "Diwali", "Christmas Day", "Eid-ul-Fitr", "Eid-ul-Zuha",
    "Muharram", "Utkala Dibasa"
  )) {
    return "public holiday"
  }

  if ($englishName -match "(?i)awareness month|cancer awareness month|sarcoma awareness month|pcos awareness month|constipation awareness month|brain awareness month") {
    return "awareness month"
  }

  if ($englishName -match "(?i)awareness week|nutrition week|breastfeeding week|immunodeficiency week|immunization week|newborn care week|antimicrobial awareness week|allergy week|men's health week|continence week|brain tumour awareness week") {
    return "awareness week"
  }

  if ($englishName -match "(?i)\bWorld\b|\bInternational\b|\bNational\b|Intl\.|Teachers' Day|Teachers Day|Spine Day|Day$") {
    return "awareness day"
  }

  return "festival"
}

function ConvertTo-HashtableValue($value) {
  if ($null -eq $value) { return $null }

  if ($value -is [System.Collections.IDictionary]) {
    $hash = @{}
    foreach ($key in $value.Keys) {
      $hash[$key] = ConvertTo-HashtableValue $value[$key]
    }
    return $hash
  }

  if ($value -is [System.Management.Automation.PSCustomObject]) {
    $hash = @{}
    foreach ($property in $value.PSObject.Properties) {
      $hash[$property.Name] = ConvertTo-HashtableValue $property.Value
    }
    return $hash
  }

  if ($value -is [System.Collections.IEnumerable] -and -not ($value -is [string])) {
    $list = New-Object System.Collections.ArrayList
    foreach ($item in $value) {
      [void]$list.Add((ConvertTo-HashtableValue $item))
    }
    return $list
  }

  return $value
}

function Add-Event([hashtable]$target, [string]$dateKey, [string]$name, [string]$type) {
  if (-not $target.ContainsKey($dateKey)) {
    $target[$dateKey] = New-Object System.Collections.Generic.List[object]
  }
  $target[$dateKey].Add([ordered]@{
    name = $name
    type = $type
  })
}

$rawText = Get-Content -Encoding UTF8 $SourcePath
$parsedDates = @{}
$currentMonth = $null

foreach ($line in $rawText) {
  $trimmed = $line.Trim()
  if (-not $trimmed) { continue }

  if ($trimmed -match '^--- .*?\(([^)]+)\)') {
    $monthName = $matches[1]
    if ($monthMap.Contains($monthName)) {
      $currentMonth = $monthMap[$monthName]
    }
    continue
  }

  if (-not $currentMonth) { continue }

  if ($trimmed -match '^ତା([୦-୯]+):\s*(.+)$') {
    $day = (Convert-OriyaDigits $matches[1]).PadLeft(2, "0")
    $dateKey = "$currentMonth-$day"
    $items = New-Object System.Collections.Generic.List[string]

    foreach ($part in (Split-CommaTopLevel $matches[2])) {
      foreach ($atomic in (Expand-AtomicEvents $part)) {
        $clean = ($atomic -replace "^\s+|\s+$", "") -replace " \(Starts\)", ""
        if ($clean) { [void]$items.Add($clean) }
      }
    }

    $parsedDates[$dateKey] = $items
  }
}

$englishJsonPath = Join-Path $BaseDir "2026\English.json"
$hindiJsonPath = Join-Path $BaseDir "2026\Hindi.json"
$odiaJsonPath = Join-Path $BaseDir "2026\Odia.json"

$englishJson = ConvertTo-HashtableValue (Get-Content -Raw -Encoding UTF8 $englishJsonPath | ConvertFrom-Json)
$hindiJson = ConvertTo-HashtableValue (Get-Content -Raw -Encoding UTF8 $hindiJsonPath | ConvertFrom-Json)
$odiaJson = ConvertTo-HashtableValue (Get-Content -Raw -Encoding UTF8 $odiaJsonPath | ConvertFrom-Json)

foreach ($dateKey in $parsedDates.Keys) {
  $englishEvents = New-Object System.Collections.Generic.List[object]
  $hindiEvents = New-Object System.Collections.Generic.List[object]
  $odiaEvents = New-Object System.Collections.Generic.List[object]

  foreach ($rawEvent in $parsedDates[$dateKey]) {
    $englishName = Get-EnglishName $rawEvent
    $eventType = Get-EventType $englishName

    $englishEvents.Add([ordered]@{
      name = $englishName
      type = $eventType
    })

    $hindiEvents.Add([ordered]@{
      name = Get-HindiName $rawEvent
      type = $hindiTypeMap[$eventType]
    })

    $odiaEvents.Add([ordered]@{
      name = Get-OdiaName $rawEvent
      type = $odiaTypeMap[$eventType]
    })
  }

  $englishJson["2026"][$dateKey] = $englishEvents
  $hindiJson["2026"][$dateKey] = $hindiEvents
  $odiaJson["2026"][$dateKey] = $odiaEvents
}

$sortedEnglish = [ordered]@{ "2026" = [ordered]@{} }
$sortedHindi = [ordered]@{ "2026" = [ordered]@{} }
$sortedOdia = [ordered]@{ "2026" = [ordered]@{} }

foreach ($key in ($englishJson["2026"].Keys | Sort-Object)) {
  $sortedEnglish["2026"][$key] = $englishJson["2026"][$key]
}
foreach ($key in ($hindiJson["2026"].Keys | Sort-Object)) {
  $sortedHindi["2026"][$key] = $hindiJson["2026"][$key]
}
foreach ($key in ($odiaJson["2026"].Keys | Sort-Object)) {
  $sortedOdia["2026"][$key] = $odiaJson["2026"][$key]
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($englishJsonPath, (($sortedEnglish | ConvertTo-Json -Depth 10) + "`n"), $utf8NoBom)
[System.IO.File]::WriteAllText($hindiJsonPath, (($sortedHindi | ConvertTo-Json -Depth 10) + "`n"), $utf8NoBom)
[System.IO.File]::WriteAllText($odiaJsonPath, (($sortedOdia | ConvertTo-Json -Depth 10) + "`n"), $utf8NoBom)
