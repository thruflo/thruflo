function (doc) {
  if (doc.doc_type == 'Document') {
    var path = doc.path + doc.filename;
    if (path.substr(0, 1) == '/') {
      path = path.slice(1);
    }
    emit([doc.repository, path], [doc._rev, doc.mod])
  };
};
