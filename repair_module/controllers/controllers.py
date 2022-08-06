# -*- coding: utf-8 -*-
# from odoo import http


# class RepairModule(http.Controller):
#     @http.route('/repair_module/repair_module/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/repair_module/repair_module/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('repair_module.listing', {
#             'root': '/repair_module/repair_module',
#             'objects': http.request.env['repair_module.repair_module'].search([]),
#         })

#     @http.route('/repair_module/repair_module/objects/<model("repair_module.repair_module"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('repair_module.object', {
#             'object': obj
#         })
