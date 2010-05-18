function (doc) {
  emit([
      doc.account_id, 
      doc.doc_type, 
      doc.slug ? doc.slug : null, 
      doc.mod
    ], 
    null
  );
}