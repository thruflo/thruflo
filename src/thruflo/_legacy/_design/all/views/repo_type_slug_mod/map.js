function (doc) {
  emit([
      doc.repository ? doc.repository : null, 
      doc.doc_type, 
      doc.slug ? doc.slug : null,
      doc.mod
    ], 
    null
  );
}
