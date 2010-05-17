function (doc) {
  if (doc.slug) {
    emit([doc.account_id, doc.doc_type, doc.slug, doc.mod], null);
  }
}