# Using Argyll v3.4.1 to generate substitute for Spyder ColorChecker24

## Commands

### Generate

```shell
targen -v -d4 -f24 -g6 -G -e0 -B0 -l400 ColorChecker24

d:\Tools\Argyll_V3.4.1\bin\printtarg -v -iSS -r -n -T300 -p4x6 -m0 -a3 ColorChecker24
```

### Scan from txt

```shell
type input.txt | d:\Tools\Argyll_V3.4.1\bin\chartread -xl -F6 -Q1964_10 -S chart-name
```

### Generate color profile

```shell
```

### Correct

d:\Tools\Argyll_V3.4.1\bin\cctiff -v -p -ir -db selphy-inv.icm ColorChecker24.tif ColorChecker24-relative.tif

