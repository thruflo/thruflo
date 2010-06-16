function (doc) {
  if (doc.doc_type == 'Repository') {
    emit([doc.owner, doc.name], null);
  }
}