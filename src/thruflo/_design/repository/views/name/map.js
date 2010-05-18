function (doc) {
  emit([
      doc.account_id, 
      doc.name
    ],
    null
  );
}