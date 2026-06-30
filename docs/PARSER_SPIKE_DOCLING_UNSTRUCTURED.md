# Parser spike Docling vs Unstructured

Questo spike resta fuori dal flusso produttivo e confronta solo snapshot locali
su fixture sintetiche. Serve a capire quale parser promette il miglior recupero
di testo e intestazioni tabellari prima di introdurre una vera estrazione.

## Comando

```powershell
python -m virgilio_connector compare-parser-fixtures `
  --catalog local_connector\tests\fixtures\parser_spike\catalog.json `
  --snapshots-dir local_connector\tests\fixtures\parser_spike\snapshots `
  --human
```

Output atteso sul catalogo iniziale:

- `docling` migliore sulla fixture `invoice_pdf` grazie al recupero completo
  delle intestazioni tabellari.
- `unstructured` migliore sulla fixture `minutes_docx` per copertura testuale
  piena senza warning.

## Struttura input

- `catalog.json`: elenco fixture con termini obbligatori e intestazioni attese.
- `snapshots/<parser>/<fixture>.json`: testo estratto, tabelle e warning.

## Limiti

- Nessuna dipendenza Docling/Unstructured e nessuna rete.
- Nessuna estrazione reale di PDF/DOCX/XLSX: gli snapshot sono sintetici.
- Il report serve solo a guidare il prossimo task `Estrazione testo e tabelle senza AI`.
