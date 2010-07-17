function (doc) {
  if (doc.doc_type == 'Document') {
    emit([doc.repository, doc.mod], [doc._rev, doc.filename])
  };
};
