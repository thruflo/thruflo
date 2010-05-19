function (doc) {
  emit([
      doc.account_id, 
      doc.owner,
      doc.name
    ],
    null
  );
}