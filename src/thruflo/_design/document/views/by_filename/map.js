function (doc) {
  if (doc.doc_type == 'Document') {
    emit([doc.repository, doc.filename], [doc._rev, doc.mod])
  };
};
