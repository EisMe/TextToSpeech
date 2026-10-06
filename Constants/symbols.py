# Commas and full stops are NOT removed here: they are kept until
# tokenization, where ',' becomes a double pause (<s><s>) and '.', '!', '?'
# become an end-of-sentence pause (<eos>).
symbols_to_remove = [
        '„','“','"', "'", ';', ':', '(', ')', '[', ']', '{', '}', '@', '#', '/', '\\', '|', '~'
    ]
symbols_to_expand = {
    "&" : "და",
    "%" : "პროცენტი",
    "+" : "პლიუს",
    "-" : "მინუს",
    "=" : "ტოლი",
    "$" : "დოლარი",
    "€" : "ევრო",
    "₾" : "ლარი",
    "₤" : "ფუნტი",
    "<" : "ნაკლებია",
    ">" : "მეტია"
}