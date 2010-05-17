function (doc) {
  if (doc.doc_type == 'ProjectSection') {
    emit([doc.account_id, doc.parent_id, doc.section_type, doc.branch], null);
  }
}
