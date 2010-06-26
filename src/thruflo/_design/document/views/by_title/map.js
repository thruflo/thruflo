function (doc) {
  if (doc.doc_type == 'Document') {
    emit([doc.repository, doc.title], [doc._rev, doc.mod])
  };
};
