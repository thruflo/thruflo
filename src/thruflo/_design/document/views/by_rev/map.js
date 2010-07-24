function (doc) {
  if (doc.doc_type == 'Document') {
    emit([doc._id, doc._rev], null);
  };
};
