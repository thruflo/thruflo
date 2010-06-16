function (doc) {
  if (doc.doc_type == 'User') {
    var i = 0,
        l = doc.repositories.length;
    for (i; i < l; i++) {
      emit([doc.repositories[i], doc.mod], null);
    }
  }
}