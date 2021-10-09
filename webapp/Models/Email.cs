

using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Indexes.Models;
using System;
using System.Text.Json.Serialization;

namespace webapp.Models
{
public partial class Email
{
    [SimpleField(IsFilterable = true, IsKey = true)]
    public string MessageId { get; set; }

    [SearchableField(IsFilterable = true, IsSortable = true, IsFacetable = true, AnalyzerName = LexicalAnalyzerName.Values.EnLucene)]
    public string MessageSubject { get; set; }

    [SearchableField(IsFilterable = true, IsSortable = true, IsFacetable = true)]
    public string MessageFrom { get; set; }

    [SearchableField(IsFilterable = true, IsSortable = true, IsFacetable = true)]
    public string MessageTo { get; set; }

    [SearchableField(AnalyzerName = LexicalAnalyzerName.Values.EnLucene)]
    public string MessageContent { get; set; }

    [SearchableField(IsFilterable = true, IsSortable = true, IsFacetable = true)]
    public  DateTimeOffset? MessageDate { get; set; }

}
}