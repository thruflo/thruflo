function (doc) {
  if (doc.slug) {
    emit([doc.doc_type, doc.slug, doc.mod], null);
  }
}