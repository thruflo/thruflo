function (doc) {
  if (doc.doc_type == 'Blob') {
    emit(doc.latest_commit, null);
  }
}