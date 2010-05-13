function (doc) {
  if (doc.doc_type == 'Template') {
    emit(doc._id, null);
  }
}