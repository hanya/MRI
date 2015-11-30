
# Tips

The way to use MRI.

## Detect Changing of Property Value

If you want to change property of the object but you do not know its name of the property. However you can change it through UI. Try the following instruction to know changes of the property values.

For example, a way to know changes of the cell property on Calc, using Diff function of MRI.

There is an optional setting for Asian Typography on Format Cells dialog. Now "Apply list of forbidden characters to the beginning and end of lines" is choosen for the target to find its property name. (This setting can be seen if you enabled Asian languages to use.)

1. Create new Calc spreadsheet document.
2. Put cell cursor on A1 cell.
3. Choose Tools - Add-Ons - MRI <- selection from the main menu.
4. MRI window is opened, stay it on there opened.
5. Right click and choose Format Cells entry from the context menu.
6. Open "Asian Typography" tab and change the state of "Apply list of forbidden characters to the beginning and end of lines" check box.
7. Push OK button to apply the change.
8. Choose Tools - Add-Ons - MRI <- selection from the main menu one more time.
9. Choose File - Diff entry on newly opened MRI window.
10. The list box is shown which shows list of opened MRI window, choose the window which is opened previously.
11. Writer document is created, which shows differences about these properties.
12. Difference is shown with red marker.
13. The property ParaIsForbiddenRules is changed.
